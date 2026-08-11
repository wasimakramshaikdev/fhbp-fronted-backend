from datetime import date, datetime, timedelta, timezone
from django.test import TestCase
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, UserRole, OwnerProfile
from apps.accounts.authentication import JWTTokenService
from apps.halls.models import Hall, HallApprovalStatus, HallStatus
from apps.availability.models import TimeSlot, SlotStatus, HallSlotAvailability
from apps.bookings.models import Booking, BookingStatus, EventType
from apps.bookings.services.booking import BookingService
from apps.bookings.tasks import expire_unpaid_holds, auto_complete_past_events
from apps.notifications.models import Notification, NotificationType
from apps.notifications.tasks import send_email_notification_task, send_in_app_notification_task, send_balance_reminders

class NotificationAndCeleryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        # Owner
        self.owner = User.objects.create_user(
            email="owner_notif@example.com",
            password="Password123!",
            full_name="K. Prasad",
            role=UserRole.OWNER
        )
        OwnerProfile.objects.create(user=self.owner, business_name="Prasad Banquets", city="Hyderabad")
        self.owner_token = JWTTokenService.generate_tokens_for_user(self.owner)['access_token']

        # Customer
        self.customer = User.objects.create_user(
            email="cust_notif@example.com",
            password="Password123!",
            full_name="Divya Rao",
            role=UserRole.CUSTOMER,
            phone="+919876542222"
        )
        self.customer_token = JWTTokenService.generate_tokens_for_user(self.customer)['access_token']

        # Hall
        self.hall = Hall.objects.create(
            owner=self.owner,
            name="Prasad Royal Banquet",
            address_line1="Gachibowli Main Rd",
            city="Hyderabad",
            locality="Gachibowli",
            min_capacity=100,
            max_capacity=500,
            base_price_morning=30000,
            base_price_evening=45000,
            base_price_full_day=70000,
            advance_percentage=20,
            approval_status=HallApprovalStatus.APPROVED,
            status=HallStatus.ACTIVE
        )

    def test_notification_feed_and_unread_counter(self):
        # Create 2 unread notifications
        Notification.objects.create(
            user=self.customer,
            title="Booking Request Received",
            message="Your reservation is pending owner confirmation",
            type=NotificationType.BOOKING_CREATED
        )
        Notification.objects.create(
            user=self.customer,
            title="Payment Receipt",
            message="Your advance payment has been confirmed",
            type=NotificationType.PAYMENT_SUCCESS
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.customer_token}")

        # Check counter
        count_res = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(count_res.status_code, status.HTTP_200_OK)
        self.assertEqual(count_res.data['data']['unread_count'], 2)

        # List notifications
        list_res = self.client.get('/api/v1/notifications/')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data['data']), 2)

        # Mark all as read
        read_all_res = self.client.post('/api/v1/notifications/read-all/')
        self.assertEqual(read_all_res.status_code, status.HTTP_200_OK)

        # Counter is now 0
        count_after = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(count_after.data['data']['unread_count'], 0)

    def test_email_task_execution(self):
        result = send_email_notification_task(
            recipient_email="test@example.com",
            subject="Test Subject",
            body="Test Message Body"
        )
        self.assertTrue(result)

    def test_expire_unpaid_holds_celery_beat_task(self):
        # Create booking that expired 5 minutes ago
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        booking = BookingService.create_booking_intent(
            customer=self.customer,
            hall=self.hall,
            event_type=EventType.WEDDING,
            event_date=date(2026, 9, 15),
            time_slot=TimeSlot.EVENING,
            guest_count=200,
            contact_name="Divya",
            contact_phone="+919876542222"
        )
        booking.expires_at = past_time
        booking.save()

        # Slot should initially be HELD
        slot_rec = HallSlotAvailability.objects.get(hall=self.hall, date="2026-09-15", slot=TimeSlot.EVENING)
        self.assertEqual(slot_rec.status, SlotStatus.HELD)

        # Run Celery Beat Expire Task
        released_count = expire_unpaid_holds()
        self.assertGreaterEqual(released_count, 1)

        # Booking is now cancelled/expired and slot is OPEN
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CANCELLED_BY_CUSTOMER)

        slot_rec.refresh_from_db()
        self.assertEqual(slot_rec.status, SlotStatus.OPEN)

    def test_auto_complete_past_events_task(self):
        # Create confirmed booking in past
        past_date = date(2026, 1, 15)
        booking = Booking.objects.create(
            customer=self.customer,
            hall=self.hall,
            event_type=EventType.WEDDING,
            event_date=past_date,
            time_slot=TimeSlot.EVENING,
            guest_count=200,
            contact_name="Divya",
            contact_phone="+919876542222",
            hall_rent=45000,
            subtotal=45000,
            tax_amount=8100,
            total_amount=53100,
            advance_amount=10620,
            balance_amount=42480,
            amount_paid=53100,
            status=BookingStatus.CONFIRMED
        )

        completed_count = auto_complete_past_events()
        self.assertGreaterEqual(completed_count, 1)

        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.COMPLETED)
