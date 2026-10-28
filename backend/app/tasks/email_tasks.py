import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_otp_email(self, email: str, otp: str, otp_type: str) -> None:
    """
    Send OTP code to user email.
    otp_type: 'email_verify' | 'password_reset'
    Subject line differs per type.
    Retries up to 3 times on SMTP failure.
    """
    subject = (
        "Verify your email"
        if otp_type == "email_verify"
        else "Reset your password"
    )
    logger.info("Sending OTP email to %s subject=%s", email, subject)
    # TODO: implement actual SMTP sending via aiosmtplib in a sync wrapper


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: int) -> None:
    """
    Sent after email verification.
    Reader: welcome + browse books CTA.
    Publisher: welcome + KYC next steps instructions.
    """
    logger.info("Sending welcome email for user_id=%s", user_id)
    # TODO: implement actual SMTP sending


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_kyc_status_email(
    self, publisher_id: int, status: str, reason: str | None = None
) -> None:
    """
    status: 'submitted' | 'approved' | 'rejected' | 'resubmission_requested'
    Sends decision email to publisher with clear next steps.
    """
    logger.info(
        "Sending KYC status email for publisher_id=%s status=%s",
        publisher_id,
        status,
    )
    # TODO: implement actual SMTP sending


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_book_status_email(
    self, book_id: int, status: str, reason: str | None = None
) -> None:
    """
    status: 'approved' | 'rejected'
    Includes rejection reason and link to edit book.
    """
    logger.info(
        "Sending book status email for book_id=%s status=%s", book_id, status
    )
    # TODO: implement actual SMTP sending


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_staff_welcome_email(self, email: str, temp_password: str) -> None:
    """Sent when admin creates a new staff account with a temporary password."""
    logger.info("Sending staff welcome email to %s", email)
    # TODO: implement actual SMTP sending


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_download_warning_email(
    self, user_id: int, book_id: int, warning_type: str
) -> None:
    """
    warning_type: 'daily_80_percent' | 'monthly_80_percent'
    Informs reader of remaining downloads for the day/month.
    """
    logger.info(
        "Sending download warning email for user_id=%s book_id=%s type=%s",
        user_id,
        book_id,
        warning_type,
    )
    # TODO: implement actual SMTP sending
