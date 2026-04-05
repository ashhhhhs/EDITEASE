"""
Centralised email service for EditEase.

Usage
-----
In api_server.py::create_app():
    from services.email_service import mail
    mail.init_app(app)

Everywhere else:
    from services.email_service import send_verification_email, send_password_reset_email, send_invitation_email
"""

from flask_mail import Mail, Message
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import config
from utils.logger import setup_logger

logger = setup_logger("email_service")

# Declared at module level — bound to the app later via mail.init_app(app)
mail = Mail()

# Jinja2 env pointing at api/templates/email/
_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "api", "templates", "email")
_jinja_env = Environment(
    loader=FileSystemLoader(os.path.abspath(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _render(template_name: str, **ctx) -> str:
    """Render a Jinja2 email template with the given context."""
    try:
        tmpl = _jinja_env.get_template(template_name)
        return tmpl.render(**ctx)
    except Exception as exc:
        logger.error("Failed to render email template %s: %s", template_name, exc)
        raise


def send_email(to: str, subject: str, html_body: str) -> bool:
    """
    Send a single HTML email via Flask-Mail (Gmail SMTP).
    Returns True on success, False on failure.
    Falls back to a dev-mode log when MAIL_USERNAME is not configured.
    """
    if not config.MAIL_USERNAME:
        logger.warning("[DEV] Email not sent (MAIL_USERNAME not configured). To=%s | Subject=%s", to, subject)
        return False
    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            html=html_body,
            sender=config.MAIL_DEFAULT_SENDER or config.MAIL_USERNAME,
        )
        mail.send(msg)
        logger.info("Email sent to %s | Subject: %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


def send_verification_email(email: str, raw_token: str) -> bool:
    """Send an email verification link."""
    verify_url = f"{config.APP_BASE_URL}/verify-email/{raw_token}"
    html = _render("verification.html", verify_url=verify_url)
    return send_email(email, "Verify your EditEase email address", html)


def send_password_reset_email(email: str, name: str, raw_token: str) -> bool:
    """Send a password reset link."""
    reset_url = f"{config.APP_BASE_URL}/reset-password/{raw_token}"
    html = _render("password_reset.html", name=name, reset_url=reset_url)
    return send_email(email, "Reset your EditEase password", html)


def send_invitation_email(email: str, role: str, invite_url: str) -> bool:
    """Send a team invitation link."""
    html = _render("invitation.html", email=email, role=role, invite_url=invite_url)
    return send_email(email, "You've been invited to EditEase", html)
