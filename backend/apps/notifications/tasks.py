import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification, NotificationType

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def send_email_notification_task(self, recipient_email: str, subject: str, body: str, html_content: str = None):
    """
    Asynchronous Celery task for transactional email delivery with exponential backoff.
    """
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'HallBook <notifications@hallbook.in>')
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[recipient_email],
            html_message=html_content,
            fail_silently=False
        )
        logger.info(f"Email '{subject}' successfully dispatched to {recipient_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email to {recipient_email}: {exc}", exc_info=True)
        # Exponential backoff: 30s, 60s, 120s, 240s...
        countdown = 30 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@shared_task
def send_in_app_notification_task(user_id: str, title: str, message: str, notification_type: str, related_entity_type: str = "", related_entity_id: str = None):
    """
    Creates an in-app notification row for a user.
    """
    try:
        user = User.objects.get(id=user_id)
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
        return str(notification.id)
    except Exception as exc:
        logger.error(f"Failed to create in-app notification: {exc}", exc_info=True)
        return None


@shared_task
def send_balance_reminders():
    """
    Celery Beat periodic task: Scans for confirmed events within 7 days where balance is due.
    """
    from apps.bookings.models import Booking, BookingStatus
    today = datetime.now(timezone.utc).date()
    target_date = today + timedelta(days=7)

    upcoming_bookings = Booking.objects.filter(
        status=BookingStatus.CONFIRMED,
        event_date__lte=target_date,
        event_date__gte=today
    )

    reminded_count = 0
    for b in upcoming_bookings:
        balance = b.total_amount - b.amount_paid
        if balance > Decimal('0.00'):
            # Send in-app notification
            send_in_app_notification_task.delay(
                user_id=str(b.customer.id),
                title="Balance Payment Reminder",
                message=f"Your upcoming event at {b.hall.name} is on {b.event_date}. Please pay the remaining balance of ₹{balance}.",
                notification_type=NotificationType.BALANCE_DUE,
                related_entity_type="Booking",
                related_entity_id=str(b.id)
            )
            # Send Email
            send_email_notification_task.delay(
                recipient_email=b.customer.email,
                subject=f"Balance Due Reminder: #{b.booking_number} for {b.hall.name}",
                body=f"Dear {b.contact_name},\n\nYour event at {b.hall.name} is scheduled for {b.event_date}.\nOutstanding balance: ₹{balance}.\nPlease settle your balance prior to the event.\n\nHallBook Team"
            )
            reminded_count += 1

    logger.info(f"Balance reminder sweep completed. Dispatched {reminded_count} reminders.")
    return reminded_count
