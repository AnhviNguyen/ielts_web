"""Send transactional email (SMTP) with dev fallback."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


async def send_password_reset_email(*, to_email: str, reset_url: str) -> None:
    subject = "LinguaIELTS — Đặt lại mật khẩu"
    body = (
        "Bạn đã yêu cầu đặt lại mật khẩu LinguaIELTS.\n\n"
        f"Nhấn vào liên kết sau (hết hạn sau {settings.PASSWORD_RESET_EXPIRE_HOURS} giờ):\n"
        f"{reset_url}\n\n"
        "Nếu bạn không yêu cầu, hãy bỏ qua email này."
    )

    if not smtp_configured():
        logger.warning(
            "SMTP not configured — password reset link for %s: %s",
            to_email,
            reset_url,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Password reset email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send password reset email: %s", exc)
        raise


async def send_verification_email(*, to_email: str, code: str) -> None:
    """Send a 6-digit OTP to verify the user's email address."""
    subject = "LinguaIELTS — Xác minh địa chỉ email"
    body = (
        "Chào bạn,\n\n"
        "Mã xác minh email LinguaIELTS của bạn là:\n\n"
        f"    {code}\n\n"
        f"Mã có hiệu lực trong 15 phút.\n"
        "Nếu bạn không đăng ký tài khoản, hãy bỏ qua email này.\n\n"
        "— LinguaIELTS"
    )

    if not smtp_configured():
        logger.warning(
            "SMTP not configured — verification code for %s: %s",
            to_email,
            code,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Verification email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send verification email: %s", exc)
        raise


async def send_daily_study_reminder_email(
    *,
    to_email: str,
    full_name: str,
    streak: int,
) -> None:
    subject = "LinguaIELTS — Nhắc luyện tập hôm nay"
    body = (
        f"Xin chào {full_name},\n\n"
        f"Đừng quên luyện IELTS hôm nay để giữ streak ({streak} ngày).\n"
        "Mở Dashboard → Study Plan để xem nhiệm vụ ưu tiên.\n\n"
        "Chúc bạn học hiệu quả!\n— LinguaIELTS"
    )

    if not smtp_configured():
        logger.warning("SMTP not configured — daily reminder for %s skipped", to_email)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Daily study reminder sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send daily reminder: %s", exc)
        raise
