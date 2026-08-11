import logging
from datetime import datetime, timezone
from django.db.models import Q
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from apps.core.responses import api_response
from apps.core.pagination import StandardPagination
from apps.core.services.audit import AuditService
from apps.accounts.permissions import IsOwnerRole, IsAdminRole, IsOwnerOrAdmin
from apps.halls.models import Hall, HallImage, Amenity, HallApprovalStatus, HallStatus
from apps.halls.serializers import (
    AmenitySerializer,
    HallImageSerializer,
    HallListSerializer,
    HallDetailSerializer,
    HallCreateUpdateSerializer,
    AdminHallApprovalSerializer,
)

logger = logging.getLogger(__name__)

class PublicHallListView(APIView):
    """
    Public search endpoint returning only APPROVED & ACTIVE function halls.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        queryset = Hall.objects.filter(
            approval_status=HallApprovalStatus.APPROVED,
            status=HallStatus.ACTIVE
        ).select_related('owner', 'owner__owner_profile').prefetch_related('amenities', 'images')

        # Filters
        q = request.query_params.get('q')
        city = request.query_params.get('city')
        locality = request.query_params.get('locality')
        hall_type = request.query_params.get('hall_type')
        guests = request.query_params.get('guests')
        capacity_min = request.query_params.get('capacity_min')
        capacity_max = request.query_params.get('capacity_max')
        price_min = request.query_params.get('price_min')
        price_max = request.query_params.get('price_max')
        min_rating = request.query_params.get('min_rating')
        amenities = request.query_params.getlist('amenities')
        sort = request.query_params.get('sort', 'recommended')

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(locality__icontains=q) |
                Q(address_line1__icontains=q)
            )

        if city:
            queryset = queryset.filter(city__iexact=city)
        if locality:
            queryset = queryset.filter(locality__iexact=locality)
        if hall_type:
            queryset = queryset.filter(hall_type=hall_type)
        if guests:
            try:
                g_val = int(guests)
                queryset = queryset.filter(min_capacity__lte=g_val, max_capacity__gte=g_val)
            except ValueError:
                pass
        if capacity_min:
            try:
                queryset = queryset.filter(max_capacity__gte=int(capacity_min))
            except ValueError:
                pass
        if capacity_max:
            try:
                queryset = queryset.filter(min_capacity__lte=int(capacity_max))
            except ValueError:
                pass
        if price_min:
            try:
                queryset = queryset.filter(base_price_morning__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                queryset = queryset.filter(base_price_morning__lte=float(price_max))
            except ValueError:
                pass
        if min_rating:
            try:
                queryset = queryset.filter(avg_rating__gte=float(min_rating))
            except ValueError:
                pass
        if amenities:
            for am in amenities:
                if am.strip():
                    queryset = queryset.filter(amenities__slug=am.strip())

        # Sorting
        if sort == 'price_asc':
            queryset = queryset.order_by('base_price_morning')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-base_price_morning')
        elif sort == 'rating' or sort == 'rating_desc':
            queryset = queryset.order_by('-avg_rating', '-review_count')
        elif sort == 'capacity_desc':
            queryset = queryset.order_by('-max_capacity')
        elif sort == 'capacity_asc':
            queryset = queryset.order_by('min_capacity')
        else:
            # Recommended sort: highest rated + review count + newest
            queryset = queryset.order_by('-avg_rating', '-review_count', '-created_at')

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = HallListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PublicFeaturedHallsView(APIView):
    """
    Returns curated top-rated featured halls for homepage display (cached in Redis).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        cache_key = "featured_halls_homepage"
        cached_data = cache.get(cache_key)
        if cached_data:
            return api_response(data=cached_data)

        halls = Hall.objects.filter(
            approval_status=HallApprovalStatus.APPROVED,
            status=HallStatus.ACTIVE
        ).select_related('owner', 'owner__owner_profile').prefetch_related('amenities', 'images').order_by('-avg_rating', '-created_at')[:6]

        serializer = HallListSerializer(halls, many=True)
        cache.set(cache_key, serializer.data, timeout=300) # 5 minutes cache
        return api_response(data=serializer.data)


class PublicAmenityListView(APIView):
    """Catalog of active venue amenities (cached in Redis)."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        cache_key = "public_amenities_catalog"
        cached_data = cache.get(cache_key)
        if cached_data:
            return api_response(data=cached_data)

        amenities = Amenity.objects.filter(is_active=True).order_by('name')
        serializer = AmenitySerializer(amenities, many=True)
        cache.set(cache_key, serializer.data, timeout=3600) # 1 hour cache
        return api_response(data=serializer.data)


class PublicHallDetailView(APIView):
    """
    Public detailed view of a single function hall by slug or UUID.
    Unapproved halls are restricted unless requested by owner or admin.
    """
    permission_classes = [AllowAny]

    def get(self, request, id_or_slug):
        import uuid
        is_uuid = False
        try:
            uuid.UUID(str(id_or_slug))
            is_uuid = True
        except (ValueError, TypeError, AttributeError):
            is_uuid = False

        if is_uuid:
            query = Q(id=id_or_slug) | Q(slug=id_or_slug)
        else:
            query = Q(slug=id_or_slug)

        hall = Hall.objects.filter(query).select_related('owner', 'owner__owner_profile').prefetch_related('amenities', 'images').first()
        if not hall:
            return api_response(
                message="Function hall not found.",
                status_code=status.HTTP_404_NOT_FOUND,
                success=False,
                code="NOT_FOUND"
            )

        # Access check for non-approved listings
        if hall.approval_status != HallApprovalStatus.APPROVED:
            user = request.user
            if not user or not user.is_authenticated or (user != hall.owner and not user.is_admin):
                return api_response(
                    message="This venue listing is currently under review or inactive.",
                    status_code=status.HTTP_404_NOT_FOUND,
                    success=False,
                    code="NOT_PUBLIC"
                )

        serializer = HallDetailSerializer(hall)
        return api_response(data=serializer.data)


class OwnerHallListCreateView(APIView):
    """
    Lists all halls belonging to the authenticated Owner, or creates a new draft listing.
    """
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get(self, request):
        halls = Hall.objects.filter(owner=request.user).prefetch_related('amenities', 'images').order_by('-created_at')
        serializer = HallDetailSerializer(halls, many=True)
        return api_response(data=serializer.data)

    def post(self, request):
        serializer = HallCreateUpdateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return api_response(
                message="Listing validation failed.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                code="VALIDATION_ERROR"
            )

        hall = serializer.save()
        AuditService.log_action(
            actor=request.user,
            action="HALL_CREATED_DRAFT",
            obj=hall,
            ip_address=request.META.get('REMOTE_ADDR'),
            changes={"name": hall.name, "locality": hall.locality}
        )

        return api_response(
            data=HallDetailSerializer(hall).data,
            message="Venue listing created successfully as Draft.",
            status_code=status.HTTP_201_CREATED
        )


class OwnerHallDetailView(APIView):
    """
    Retrieves, updates, or deletes an owner's specific function hall listing.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self, request, pk):
        hall = Hall.objects.filter(id=pk).prefetch_related('amenities', 'images').first()
        if not hall:
            return None
        if hall.owner != request.user and not request.user.is_admin:
            return "FORBIDDEN"
        return hall

    def get(self, request, pk):
        hall = self.get_object(request, pk)
        if hall is None:
            return api_response(message="Venue not found.", status_code=status.HTTP_404_NOT_FOUND, success=False)
        if hall == "FORBIDDEN":
            return api_response(message="You do not have permission to access this venue.", status_code=status.HTTP_403_FORBIDDEN, success=False)
        return api_response(data=HallDetailSerializer(hall).data)

    def patch(self, request, pk):
        hall = self.get_object(request, pk)
        if hall is None:
            return api_response(message="Venue not found.", status_code=status.HTTP_404_NOT_FOUND, success=False)
        if hall == "FORBIDDEN":
            return api_response(message="You do not have permission to modify this venue.", status_code=status.HTTP_403_FORBIDDEN, success=False)

        serializer = HallCreateUpdateSerializer(hall, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return api_response(
                message="Update validation failed.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                code="VALIDATION_ERROR"
            )

        updated_hall = serializer.save()
        # Invalidate featured cache
        cache.delete("featured_halls_homepage")

        AuditService.log_action(
            actor=request.user,
            action="HALL_UPDATED",
            obj=updated_hall,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return api_response(
            data=HallDetailSerializer(updated_hall).data,
            message="Venue listing updated successfully."
        )


class OwnerHallSubmitView(APIView):
    """
    Submits a draft or rejected hall listing to the Super Admin queue for verification & approval.
    """
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def post(self, request, pk):
        hall = Hall.objects.filter(id=pk, owner=request.user).first()
        if not hall:
            return api_response(message="Venue not found.", status_code=status.HTTP_404_NOT_FOUND, success=False)

        if hall.approval_status not in [HallApprovalStatus.DRAFT, HallApprovalStatus.REJECTED]:
            return api_response(
                message=f"Cannot submit venue in '{hall.approval_status}' state.",
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                code="INVALID_STATE"
            )

        hall.approval_status = HallApprovalStatus.UNDER_REVIEW
        hall.rejection_reason = ""
        hall.save()

        AuditService.log_action(
            actor=request.user,
            action="HALL_SUBMITTED_FOR_REVIEW",
            obj=hall,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return api_response(
            data=HallDetailSerializer(hall).data,
            message="Venue submitted for platform review. An administrator will verify and approve your listing."
        )


class OwnerHallToggleStatusView(APIView):
    """
    Enables/disables public availability for approved listings.
    """
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def post(self, request, pk):
        hall = Hall.objects.filter(id=pk, owner=request.user).first()
        if not hall:
            return api_response(message="Venue not found.", status_code=status.HTTP_404_NOT_FOUND, success=False)

        if hall.approval_status != HallApprovalStatus.APPROVED:
            return api_response(
                message="Only approved venues can toggle operational status.",
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False
            )

        hall.status = HallStatus.INACTIVE if hall.status == HallStatus.ACTIVE else HallStatus.ACTIVE
        hall.save()
        cache.delete("featured_halls_homepage")

        AuditService.log_action(
            actor=request.user,
            action="HALL_STATUS_TOGGLED",
            obj=hall,
            changes={"status": hall.status}
        )

        return api_response(
            data={"status": hall.status},
            message=f"Venue status updated to {hall.status}."
        )


class OwnerHallImageUploadView(APIView):
    """
    Adds images to hall gallery.
    """
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def post(self, request, pk):
        hall = Hall.objects.filter(id=pk, owner=request.user).first()
        if not hall:
            return api_response(message="Venue not found.", status_code=status.HTTP_404_NOT_FOUND, success=False)

        image_urls = request.data.get('images', [])
        if isinstance(image_urls, str):
            image_urls = [image_urls]

        if not image_urls:
            return api_response(
                message="No image URLs provided.",
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False
            )

        from apps.halls.serializers import validate_safe_image_url
        validated_urls = []
        for url in image_urls:
            try:
                validated_urls.append(validate_safe_image_url(url))
            except Exception as e:
                return api_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST, success=False)

        created_images = []
        existing_count = hall.images.count()
        for idx, url in enumerate(validated_urls):
            img = HallImage.objects.create(
                hall=hall,
                image_url=url,
                sort_order=existing_count + idx,
                is_primary=(existing_count == 0 and idx == 0)
            )
            created_images.append(img)

        return api_response(
            data=HallImageSerializer(created_images, many=True).data,
            message="Images uploaded successfully."
        )


class OwnerHallImageDeleteView(APIView):
    """
    Deletes an image from a hall's gallery.
    """
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def delete(self, request, pk, img_id):
        img = HallImage.objects.filter(id=img_id, hall_id=pk, hall__owner=request.user).first()
        if not img:
            return api_response(message="Image not found.", status_code=status.HTTP_404_NOT_FOUND, success=False)

        was_primary = img.is_primary
        hall = img.hall
        img.delete()

        if was_primary:
            next_img = hall.images.first()
            if next_img:
                next_img.is_primary = True
                next_img.save()

        return api_response(message="Image deleted successfully.")


class AdminHallListView(APIView):
    """
    Super Admin listing of all halls with approval status filtering.
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        status_filter = request.query_params.get('status')
        queryset = Hall.objects.all().select_related('owner', 'owner__owner_profile').prefetch_related('amenities', 'images').order_by('-created_at')

        if status_filter:
            queryset = queryset.filter(approval_status=status_filter)

        serializer = HallDetailSerializer(queryset, many=True)
        return api_response(data=serializer.data)


class AdminHallActionView(APIView):
    """
    Super Admin decision: APPROVE, REJECT, or SUSPEND listing.
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        hall = Hall.objects.filter(id=pk).first()
        if not hall:
            return api_response(message="Venue not found.", status_code=status.HTTP_404_NOT_FOUND, success=False)

        serializer = AdminHallApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                message="Decision payload invalid.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False
            )

        action = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')

        if action == 'APPROVE':
            hall.approval_status = HallApprovalStatus.APPROVED
            hall.status = HallStatus.ACTIVE
            hall.rejection_reason = ""
            hall.approved_by = request.user
            hall.approved_at = datetime.now(timezone.utc)
            hall.save()
            cache.delete("featured_halls_homepage")

            AuditService.log_action(
                actor=request.user,
                action="ADMIN_APPROVED_HALL",
                obj=hall,
                changes={"status": "APPROVED"}
            )
            return api_response(
                data=HallDetailSerializer(hall).data,
                message=f"Venue '{hall.name}' has been approved and is now live on the marketplace."
            )

        elif action == 'REJECT':
            hall.approval_status = HallApprovalStatus.REJECTED
            hall.rejection_reason = reason
            hall.save()
            cache.delete("featured_halls_homepage")

            AuditService.log_action(
                actor=request.user,
                action="ADMIN_REJECTED_HALL",
                obj=hall,
                changes={"status": "REJECTED", "reason": reason}
            )
            return api_response(
                data=HallDetailSerializer(hall).data,
                message=f"Venue '{hall.name}' has been rejected."
            )

        elif action == 'SUSPEND':
            hall.approval_status = HallApprovalStatus.SUSPENDED
            hall.status = HallStatus.INACTIVE
            hall.save()
            cache.delete("featured_halls_homepage")

            AuditService.log_action(
                actor=request.user,
                action="ADMIN_SUSPENDED_HALL",
                obj=hall,
                changes={"status": "SUSPENDED"}
            )
            return api_response(
                data=HallDetailSerializer(hall).data,
                message=f"Venue '{hall.name}' has been suspended from the marketplace."
            )
