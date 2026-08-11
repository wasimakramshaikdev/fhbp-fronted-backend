from datetime import date
from django.test import TestCase
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, UserRole, OwnerProfile
from apps.accounts.authentication import JWTTokenService
from apps.halls.models import Hall, HallApprovalStatus, HallStatus
from apps.availability.models import TimeSlot
from apps.bookings.models import Booking, BookingStatus, EventType

class DashboardDomainTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        self.owner = User.objects.create_user(
            email="owner_dash@example.com",
            password="Password123!",
            full_name="K. Naidu",
            role=UserRole.OWNER
        )
        OwnerProfile.objects.create(user=self.owner, business_name="Grand Orchid LLC", city="Hyderabad")
        self.owner_token = JWTTokenService.generate_tokens_for_user(self.owner)['access_token']

        self.customer = User.objects.create_user(
            email="cust_dash@example.com",
            password="Password123!",
            full_name="R. Sharma",
            role=UserRole.CUSTOMER
        )

        self.hall = Hall.objects.create(
            owner=self.owner,
            name="Grand Orchid Banquets",
            address_line1="Road 36, Madhapur",
            city="Hyderabad",
            locality="Madhapur",
            min_capacity=100,
            max_capacity=500,
            avg_rating=4.5,
            review_count=12,
            approval_status=HallApprovalStatus.APPROVED,
            status=HallStatus.ACTIVE
        )

        # 1. Create Pending Request
        Booking.objects.create(
            customer=self.customer,
            hall=self.hall,
            event_type=EventType.ENGAGEMENT,
            event_date=date(2026, 8, 14),
            time_slot=TimeSlot.MORNING,
            guest_count=200,
            contact_name="A. Reddy",
            contact_phone="+919876543211",
            hall_rent=30000,
            subtotal=30000,
            tax_amount=5400,
            total_amount=35400,
            advance_amount=7080,
            balance_amount=28320,
            amount_paid=7080,
            status=BookingStatus.PENDING_OWNER_CONFIRMATION
        )

        # 2. Create Confirmed Booking
        Booking.objects.create(
            customer=self.customer,
            hall=self.hall,
            event_type=EventType.WEDDING,
            event_date=date(2026, 8, 12),
            time_slot=TimeSlot.EVENING,
            guest_count=350,
            contact_name="R. Sharma",
            contact_phone="+919876543210",
            hall_rent=45000,
            subtotal=45000,
            tax_amount=8100,
            total_amount=53100,
            advance_amount=10620,
            balance_amount=42480,
            amount_paid=53100,
            status=BookingStatus.CONFIRMED
        )

    def test_owner_dashboard_overview_metrics(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.owner_token}")
        res = self.client.get('/api/v1/owner/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])

        metrics = res.data['data']['metrics']
        self.assertEqual(metrics['pending_requests'], 1)
        self.assertEqual(metrics['confirmed_this_month'], 1)
        self.assertEqual(metrics['revenue_this_month'], 53100.0)
        self.assertEqual(metrics['avg_rating'], 4.5)

        upcoming = res.data['data']['upcoming_events']
        self.assertEqual(len(upcoming), 2)
