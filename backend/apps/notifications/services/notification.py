import logging
from apps.notifications.tasks import send_email_notification_task, send_in_app_notification_task
from apps.notifications.models import NotificationType

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def notify_booking_created(booking):
        """Alerts the hall owner that a new reservation request has been submitted."""
        owner = booking.hall.owner
        title = f"New Booking Request: #{booking.booking_number}"
        msg = f"{booking.contact_name} has requested {booking.hall.name} for {booking.event_date} ({booking.time_slot}) for {booking.guest_count} guests."
        
        send_in_app_notification_task.delay(
            user_id=str(owner.id),
            title=title,
            message=msg,
            notification_type=NotificationType.BOOKING_CREATED,
            related_entity_type="Booking",
            related_entity_id=str(booking.id)
        )
        send_email_notification_task.delay(
            recipient_email=owner.email,
            subject=f"Action Required: New Booking Request for {booking.hall.name}",
            body=f"Hello,\n\nYou have received a new booking request for {booking.hall.name}.\nEvent Date: {booking.event_date}\nSlot: {booking.time_slot}\nGuests: {booking.guest_count}\n\nPlease review and confirm in your HallBook Owner Dashboard.\n\nHallBook Team"
        )

    @staticmethod
    def notify_booking_confirmed(booking):
        """Alerts the customer that the hall owner has accepted their booking."""
        customer = booking.customer
        title = f"Booking Confirmed: #{booking.booking_number}!"
        msg = f"Great news! The owner of {booking.hall.name} has confirmed your event on {booking.event_date} ({booking.time_slot})."

        send_in_app_notification_task.delay(
            user_id=str(customer.id),
            title=title,
            message=msg,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            related_entity_type="Booking",
            related_entity_id=str(booking.id)
        )
        send_email_notification_task.delay(
            recipient_email=customer.email,
            subject=f"Booking Confirmed: {booking.hall.name} on {booking.event_date}",
            body=f"Dear {booking.contact_name},\n\nYour function hall reservation at {booking.hall.name} for {booking.event_date} ({booking.time_slot}) is officially confirmed!\n\nHallBook Team"
        )

    @staticmethod
    def notify_booking_rejected(booking, reason: str = ""):
        """Alerts the customer that the hall owner declined their request."""
        customer = booking.customer
        title = f"Booking Declined: #{booking.booking_number}"
        msg = f"The owner of {booking.hall.name} was unable to accept your request for {booking.event_date}. Reason: {reason or 'Unavailable'}. Your 100% advance has been refunded."

        send_in_app_notification_task.delay(
            user_id=str(customer.id),
            title=title,
            message=msg,
            notification_type=NotificationType.BOOKING_REJECTED,
            related_entity_type="Booking",
            related_entity_id=str(booking.id)
        )
        send_email_notification_task.delay(
            recipient_email=customer.email,
            subject=f"Booking Update: #{booking.booking_number}",
            body=f"Dear {booking.contact_name},\n\nUnfortunately, {booking.hall.name} could not accept your booking for {booking.event_date}.\nReason: {reason or 'Unavailable'}\n\nYour 100% advance deposit has been refunded to your original payment method.\n\nHallBook Team"
        )

    @staticmethod
    def notify_payment_success(payment):
        """Alerts the customer of successful payment receipt."""
        customer = payment.booking.customer
        title = f"Payment Successful: {payment.payment_reference}"
        msg = f"Your payment of ₹{payment.amount} for booking #{payment.booking.booking_number} was successfully processed."

        send_in_app_notification_task.delay(
            user_id=str(customer.id),
            title=title,
            message=msg,
            notification_type=NotificationType.PAYMENT_SUCCESS,
            related_entity_type="Payment",
            related_entity_id=str(payment.id)
        )
        send_email_notification_task.delay(
            recipient_email=customer.email,
            subject=f"Payment Receipt: #{payment.payment_reference} (₹{payment.amount})",
            body=f"Dear Customer,\n\nWe have received your payment of ₹{payment.amount} for {payment.booking.hall.name}.\nYou can view and download your official GST tax invoice in your dashboard.\n\nHallBook Team"
        )

    notify_payment_received = notify_payment_success
