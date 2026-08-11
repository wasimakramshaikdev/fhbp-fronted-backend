import re
from urllib.parse import urlparse
from rest_framework import serializers
from apps.halls.models import Hall, HallImage, Amenity, HallApprovalStatus, HallStatus, HallType, CateringPolicy, CancellationPolicy

def validate_safe_image_url(url_str: str) -> str:
    """
    Validates that image URL uses HTTPS, does not contain malicious extensions (SVG, JS, HTML),
    and conforms to safe image formats (JPG, PNG, WEBP, AVIF).
    """
    if not url_str or not isinstance(url_str, str):
        raise serializers.ValidationError("Valid image URL string is required.")

    parsed = urlparse(url_str)
    if parsed.scheme not in ['http', 'https']:
        raise serializers.ValidationError("Image URL must use HTTP or HTTPS protocol.")

    path_lower = parsed.path.lower()
    
    # Block dangerous executable / script / SVG extensions
    forbidden_exts = ['.svg', '.html', '.htm', '.js', '.php', '.exe', '.sh', '.py', '.bat', '.cgi']
    for ext in forbidden_exts:
        if path_lower.endswith(ext) or f"{ext}?" in url_str.lower():
            raise serializers.ValidationError(f"File type '{ext}' is not permitted for security reasons. Use JPG, PNG, or WEBP.")

    # Safe image extensions or approved image CDN query parameters
    valid_exts = ['.jpg', '.jpeg', '.png', '.webp', '.avif']
    has_valid_ext = any(path_lower.endswith(ext) for ext in valid_exts)
    is_cdn_image = any(cdn in parsed.netloc for cdn in ['unsplash.com', 'cloudinary.com', 'amazonaws.com', 'googleusercontent.com', 'imgix.net'])

    if not (has_valid_ext or is_cdn_image):
        raise serializers.ValidationError("Image must be a valid JPG, PNG, WEBP, or AVIF file.")

    return url_str


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'slug', 'icon_name']


class HallImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HallImage
        fields = ['id', 'image_url', 'caption', 'sort_order', 'is_primary', 'created_at']


class HallListSerializer(serializers.ModelSerializer):
    """Compact summary serializer for search results and homepage listings."""
    primary_image = serializers.ReadOnlyField()
    amenities = AmenitySerializer(many=True, read_only=True)
    owner_business = serializers.CharField(source='owner.owner_profile.business_name', read_only=True)

    class Meta:
        model = Hall
        fields = [
            'id',
            'name',
            'slug',
            'address_line1',
            'city',
            'locality',
            'postal_code',
            'latitude',
            'longitude',
            'min_capacity',
            'max_capacity',
            'hall_type',
            'base_price_morning',
            'base_price_evening',
            'base_price_full_day',
            'advance_percentage',
            'catering_policy',
            'veg_plate_price',
            'non_veg_plate_price',
            'decor_price',
            'dj_price',
            'avg_rating',
            'review_count',
            'primary_image',
            'amenities',
            'owner_business',
            'status',
            'approval_status',
            'created_at'
        ]


class HallDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for public hall page and owner management."""
    images = HallImageSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_business = serializers.CharField(source='owner.owner_profile.business_name', read_only=True)
    owner_phone = serializers.CharField(source='owner.phone', read_only=True)

    class Meta:
        model = Hall
        fields = [
            'id',
            'owner_id',
            'owner_name',
            'owner_business',
            'owner_phone',
            'name',
            'slug',
            'description',
            'address_line1',
            'address_line2',
            'city',
            'locality',
            'postal_code',
            'latitude',
            'longitude',
            'min_capacity',
            'max_capacity',
            'hall_type',
            'base_price_morning',
            'base_price_evening',
            'base_price_full_day',
            'advance_percentage',
            'catering_policy',
            'veg_plate_price',
            'non_veg_plate_price',
            'decor_price',
            'dj_price',
            'cancellation_policy',
            'status',
            'approval_status',
            'rejection_reason',
            'avg_rating',
            'review_count',
            'images',
            'amenities',
            'created_at',
            'updated_at'
        ]


class HallCreateUpdateSerializer(serializers.ModelSerializer):
    amenity_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )
    initial_images = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Hall
        fields = [
            'name',
            'description',
            'address_line1',
            'address_line2',
            'city',
            'locality',
            'postal_code',
            'latitude',
            'longitude',
            'min_capacity',
            'max_capacity',
            'hall_type',
            'base_price_morning',
            'base_price_evening',
            'base_price_full_day',
            'advance_percentage',
            'catering_policy',
            'veg_plate_price',
            'non_veg_plate_price',
            'decor_price',
            'dj_price',
            'cancellation_policy',
            'amenity_ids',
            'initial_images'
        ]

    def validate_initial_images(self, value):
        if len(value) > 20:
            raise serializers.ValidationError("Maximum 20 images allowed per listing.")
        return [validate_safe_image_url(url) for url in value]

    def validate(self, attrs):
        min_cap = attrs.get('min_capacity')
        max_cap = attrs.get('max_capacity')

        if min_cap and max_cap and max_cap < min_cap:
            raise serializers.ValidationError({"max_capacity": ["Maximum capacity cannot be less than minimum capacity."]})

        if min_cap and min_cap <= 0:
            raise serializers.ValidationError({"min_capacity": ["Minimum capacity must be greater than 0."]})

        return attrs

    def create(self, validated_data):
        amenity_ids = validated_data.pop('amenity_ids', [])
        initial_images = validated_data.pop('initial_images', [])
        owner = self.context['request'].user

        hall = Hall.objects.create(
            owner=owner,
            approval_status=HallApprovalStatus.DRAFT,
            status=HallStatus.ACTIVE,
            **validated_data
        )

        if amenity_ids:
            amenities = Amenity.objects.filter(id__in=amenity_ids)
            hall.amenities.set(amenities)

        if initial_images:
            for idx, img_url in enumerate(initial_images):
                HallImage.objects.create(
                    hall=hall,
                    image_url=img_url,
                    sort_order=idx,
                    is_primary=(idx == 0)
                )

        return hall

    def update(self, instance, validated_data):
        amenity_ids = validated_data.pop('amenity_ids', None)
        validated_data.pop('initial_images', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if amenity_ids is not None:
            amenities = Amenity.objects.filter(id__in=amenity_ids)
            instance.amenities.set(amenities)

        return instance


class AdminHallApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT', 'SUSPEND'])
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        action = attrs.get('action')
        reason = attrs.get('reason')
        if action == 'REJECT' and not reason:
            raise serializers.ValidationError({"reason": ["Rejection reason is mandatory when rejecting a listing."]})
        return attrs
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'slug', 'icon_name']


class HallImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HallImage
        fields = ['id', 'image_url', 'caption', 'sort_order', 'is_primary', 'created_at']


class HallListSerializer(serializers.ModelSerializer):
    """Compact summary serializer for search results and homepage listings."""
    primary_image = serializers.ReadOnlyField()
    amenities = AmenitySerializer(many=True, read_only=True)
    owner_business = serializers.CharField(source='owner.owner_profile.business_name', read_only=True)

    class Meta:
        model = Hall
        fields = [
            'id',
            'name',
            'slug',
            'address_line1',
            'city',
            'locality',
            'postal_code',
            'latitude',
            'longitude',
            'min_capacity',
            'max_capacity',
            'hall_type',
            'base_price_morning',
            'base_price_evening',
            'base_price_full_day',
            'advance_percentage',
            'catering_policy',
            'veg_plate_price',
            'non_veg_plate_price',
            'decor_price',
            'dj_price',
            'avg_rating',
            'review_count',
            'primary_image',
            'amenities',
            'owner_business',
            'status',
            'approval_status',
            'created_at'
        ]


class HallDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for public hall page and owner management."""
    images = HallImageSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_business = serializers.CharField(source='owner.owner_profile.business_name', read_only=True)
    owner_phone = serializers.CharField(source='owner.phone', read_only=True)

    class Meta:
        model = Hall
        fields = [
            'id',
            'owner_id',
            'owner_name',
            'owner_business',
            'owner_phone',
            'name',
            'slug',
            'description',
            'address_line1',
            'address_line2',
            'city',
            'locality',
            'postal_code',
            'latitude',
            'longitude',
            'min_capacity',
            'max_capacity',
            'hall_type',
            'base_price_morning',
            'base_price_evening',
            'base_price_full_day',
            'advance_percentage',
            'catering_policy',
            'veg_plate_price',
            'non_veg_plate_price',
            'decor_price',
            'dj_price',
            'cancellation_policy',
            'status',
            'approval_status',
            'rejection_reason',
            'avg_rating',
            'review_count',
            'images',
            'amenities',
            'created_at',
            'updated_at'
        ]


class HallCreateUpdateSerializer(serializers.ModelSerializer):
    amenity_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True
    )
    initial_images = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        write_only=True
    )

    class Meta:
        model = Hall
        fields = [
            'name',
            'description',
            'address_line1',
            'address_line2',
            'city',
            'locality',
            'postal_code',
            'latitude',
            'longitude',
            'min_capacity',
            'max_capacity',
            'hall_type',
            'base_price_morning',
            'base_price_evening',
            'base_price_full_day',
            'advance_percentage',
            'catering_policy',
            'veg_plate_price',
            'non_veg_plate_price',
            'decor_price',
            'dj_price',
            'cancellation_policy',
            'amenity_ids',
            'initial_images'
        ]

    def validate(self, attrs):
        min_cap = attrs.get('min_capacity')
        max_cap = attrs.get('max_capacity')

        if min_cap and max_cap and max_cap < min_cap:
            raise serializers.ValidationError({"max_capacity": ["Maximum capacity cannot be less than minimum capacity."]})

        if min_cap and min_cap <= 0:
            raise serializers.ValidationError({"min_capacity": ["Minimum capacity must be greater than 0."]})

        return attrs

    def create(self, validated_data):
        amenity_ids = validated_data.pop('amenity_ids', [])
        initial_images = validated_data.pop('initial_images', [])
        owner = self.context['request'].user

        hall = Hall.objects.create(
            owner=owner,
            approval_status=HallApprovalStatus.DRAFT,
            status=HallStatus.ACTIVE,
            **validated_data
        )

        if amenity_ids:
            amenities = Amenity.objects.filter(id__in=amenity_ids)
            hall.amenities.set(amenities)

        if initial_images:
            for idx, img_url in enumerate(initial_images):
                HallImage.objects.create(
                    hall=hall,
                    image_url=img_url,
                    sort_order=idx,
                    is_primary=(idx == 0)
                )

        return hall

    def update(self, instance, validated_data):
        amenity_ids = validated_data.pop('amenity_ids', None)
        validated_data.pop('initial_images', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if amenity_ids is not None:
            amenities = Amenity.objects.filter(id__in=amenity_ids)
            instance.amenities.set(amenities)

        return instance


class AdminHallApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT', 'SUSPEND'])
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        action = attrs.get('action')
        reason = attrs.get('reason')
        if action == 'REJECT' and not reason:
            raise serializers.ValidationError({"reason": ["Rejection reason is mandatory when rejecting a listing."]})
        return attrs
