"""Send transactional email (SMTP) with dev fallback."""

from __future__ import annotations

import logging
import smtplib
from html import escape
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    if not settings.SMTP_HOST:
        return False
    if not _sender_address():
        return False
    if bool(settings.SMTP_USER) != bool(settings.SMTP_PASSWORD):
        logger.warning("SMTP_USER and SMTP_PASSWORD must be configured together")
        return False
    return True


def resend_configured() -> bool:
    return bool((settings.RESEND_API_KEY or "").strip() and _resend_sender_address())


def brevo_configured() -> bool:
    return bool((settings.BREVO_API_KEY or "").strip() and _brevo_sender())


def email_configured() -> bool:
    return brevo_configured() or resend_configured() or smtp_configured()


def _sender_address() -> str:
    """Return a valid RFC 5322 From value for SMTP providers such as Gmail."""
    raw_from = (settings.SMTP_FROM or "").strip()
    smtp_user = (settings.SMTP_USER or "").strip()

    parsed_name, parsed_email = parseaddr(raw_from)
    if "@" in parsed_email:
        return formataddr((parsed_name, parsed_email)) if parsed_name else parsed_email

    if "@" in smtp_user:
        display_name = raw_from or "LinguaIELTS"
        return formataddr((display_name, smtp_user))

    return ""


def _resend_sender_address() -> str:
    raw_from = (settings.RESEND_FROM or settings.SMTP_FROM or "").strip()
    parsed_name, parsed_email = parseaddr(raw_from)
    if "@" in parsed_email:
        return formataddr((parsed_name, parsed_email)) if parsed_name else parsed_email
    return ""


def _brevo_sender() -> dict[str, str] | None:
    raw_from = (settings.BREVO_FROM or settings.RESEND_FROM or settings.SMTP_FROM or "").strip()
    parsed_name, parsed_email = parseaddr(raw_from)
    if "@" not in parsed_email:
        return None
    sender = {"email": parsed_email}
    if parsed_name:
        sender["name"] = parsed_name
    return sender


def _message_sender_address() -> str:
    brevo_sender = _brevo_sender()
    if brevo_configured() and brevo_sender:
        return formataddr((brevo_sender.get("name", ""), brevo_sender["email"]))
    if resend_configured():
        return _resend_sender_address()
    return _sender_address()


async def _send_via_brevo(msg: EmailMessage) -> None:
    body = msg.get_content()
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": settings.BREVO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "sender": _brevo_sender(),
                "to": [{"email": msg["To"]}],
                "subject": msg["Subject"],
                "textContent": body,
                "htmlContent": f"<pre>{escape(body)}</pre>",
            },
        )
        response.raise_for_status()


async def _send_via_resend(msg: EmailMessage) -> None:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": _resend_sender_address(),
                "to": [msg["To"]],
                "subject": msg["Subject"],
                "text": msg.get_content(),
            },
        )
        response.raise_for_status()


def _send_message(msg: EmailMessage) -> None:
    if settings.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


async def send_password_reset_email(*, to_email: str, reset_url: str) -> None:
    subject = "LinguaIELTS — Đặt lại mật khẩu"
    body = (
        "Bạn đã yêu cầu đặt lại mật khẩu LinguaIELTS.\n\n"
        f"Nhấn vào liên kết sau (hết hạn sau {settings.PASSWORD_RESET_EXPIRE_HOURS} giờ):\n"
        f"{reset_url}\n\n"
        "Nếu bạn không yêu cầu, hãy bỏ qua email này."
    )

    if not email_configured():
        logger.warning(
            "SMTP not configured — password reset link for %s: %s",
            to_email,
            reset_url,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _message_sender_address()
    msg["To"] = to_email
    msg.set_content(body)

    try:
        if brevo_configured():
            await _send_via_brevo(msg)
        elif resend_configured():
            await _send_via_resend(msg)
        else:
            _send_message(msg)
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

    if not email_configured():
        logger.warning(
            "SMTP not configured — verification code for %s: %s",
            to_email,
            code,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _message_sender_address()
    msg["To"] = to_email
    msg.set_content(body)

    try:
        if brevo_configured():
            await _send_via_brevo(msg)
        elif resend_configured():
            await _send_via_resend(msg)
        else:
            _send_message(msg)
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

    if not email_configured():
        logger.warning("SMTP not configured — daily reminder for %s skipped", to_email)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _message_sender_address()
    msg["To"] = to_email
    msg.set_content(body)

    try:
        if brevo_configured():
            await _send_via_brevo(msg)
        elif resend_configured():
            await _send_via_resend(msg)
        else:
            _send_message(msg)
        logger.info("Daily study reminder sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send daily reminder: %s", exc)
        raise
