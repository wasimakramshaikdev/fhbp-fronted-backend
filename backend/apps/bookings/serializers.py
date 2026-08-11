from rest_framework import serializers
from apps.bookings.models import Booking, BookingStatus, EventType
from apps.availability.models import TimeSlot
from apps.halls.serializers import HallListSerializer

class BookingCreateIntentSerializer(serializers.Serializer):
    hall_id = serializers.UUIDField(required=True)
    event_type = serializers.ChoiceField(choices=EventType.choices, default=EventType.WEDDING)
    event_date = serializers.DateField(required=True)
    time_slot = serializers.ChoiceField(choices=TimeSlot.choices, required=True)
    guest_count = serializers.IntegerField(required=True, min_value=1)
    contact_name = serializers.CharField(max_length=150, required=True)
    contact_phone = serializers.CharField(max_length=20, required=True)
    special_requests = serializers.CharField(required=False, allow_blank=True, default="")
    has_catering = serializers.BooleanField(required=False, default=False)
    catering_type = serializers.ChoiceField(choices=['VEG', 'NON_VEG'], required=False, default='VEG')
    has_decor = serializers.BooleanField(required=False, default=False)
    has_dj = serializers.BooleanField(required=False, default=False)


class BookingListSerializer(serializers.ModelSerializer):
    hall_name = serializers.CharField(source='hall.name', read_only=True)
    hall_slug = serializers.CharField(source='hall.slug', read_only=True)
    hall_locality = serializers.CharField(source='hall.locality', read_only=True)
    hall_city = serializers.CharField(source='hall.city', read_only=True)
    primary_image = serializers.CharField(source='hall.primary_image', read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_number',
            'hall_id',
            'hall_name',
            'hall_slug',
            'hall_locality',
            'hall_city',
            'primary_image',
            'customer_name',
            'customer_email',
            'event_type',
            'event_date',
            'time_slot',
            'guest_count',
            'total_amount',
            'advance_amount',
            'balance_amount',
            'amount_paid',
            'status',
            'created_at'
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    hall = HallListSerializer(read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_number',
            'customer_id',
            'customer_name',
            'customer_email',
            'customer_phone',
            'contact_name',
            'contact_phone',
            'hall',
            'event_type',
            'event_date',
            'time_slot',
            'guest_count',
            'special_requests',
            'has_catering',
            'catering_plate_type',
            'catering_plate_price',
            'has_decor',
            'has_dj',
            'hall_rent',
            'catering_amount',
            'decor_amount',
            'dj_amount',
            'subtotal',
            'discount_amount',
            'tax_rate',
            'tax_amount',
            'total_amount',
            'advance_percentage',
            'advance_amount',
            'balance_amount',
            'amount_paid',
            'status',
            'owner_response_notes',
            'cancellation_reason',
            'cancellation_fee',
            'refund_amount',
            'expires_at',
            'created_at',
            'updated_at'
        ]


class BookingOwnerDecisionSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class BookingCancellationSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)
