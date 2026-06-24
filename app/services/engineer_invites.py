"""
Account invitation helpers.

Supports invite-link generation plus email delivery through either:
1. Resend API over HTTPS (works well on hosted environments)
2. SMTP when explicitly configured
3. Manual-link fallback when no provider is configured
"""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from hashlib import sha256
from html import escape
from secrets import token_urlsafe
import smtplib
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import settings


@dataclass
class InviteDeliveryResult:
    method: str
    message: str
    invite_url: Optional[str] = None


def generate_invite_token() -> str:
    return token_urlsafe(32)


def hash_invite_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def build_invite_url(token: str) -> str:
    base_url = settings.frontend_url.rstrip("/")
    params = {"token": token}
    if settings.public_backend_url:
        params["api_origin"] = settings.public_backend_url
    return f"{base_url}/setup-account?{urlencode(params)}"


def build_password_reset_url(token: str) -> str:
    base_url = settings.frontend_url.rstrip("/")
    params = {"token": token}
    if settings.public_backend_url:
        params["api_origin"] = settings.public_backend_url
    return f"{base_url}/reset-password?{urlencode(params)}"


def _render_detail_cards(lines: list[str]) -> str:
    return "".join(
        (
            '<tr>'
            '<td style="padding: 0 0 12px 0;">'
            '<div style="border:1px solid #dbeafe;border-radius:14px;padding:12px 14px;background:#f8fbff;">'
            f'<p style="margin:0;font-size:13px;line-height:1.4;color:#0f172a;font-weight:600;">{escape(line)}</p>'
            "</div>"
            "</td>"
            "</tr>"
        )
        for line in lines
    )


def _wrap_email_html(*, badge: str, title: str, intro: str, body_html: str, footer: str) -> str:
    return f"""
    <div style="margin:0;padding:32px 16px;background:#e0f2fe;background-image:linear-gradient(135deg,#0f172a 0%,#0b4a6f 48%,#22d3ee 100%);font-family:Arial,sans-serif;">
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width:640px;margin:0 auto;">
        <tr>
          <td style="padding-bottom:18px;text-align:center;">
            <span style="display:inline-block;padding:8px 14px;border-radius:999px;background:rgba(255,255,255,0.14);color:#ecfeff;font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">
              {escape(badge)}
            </span>
          </td>
        </tr>
        <tr>
          <td style="border-radius:28px;overflow:hidden;background:#ffffff;box-shadow:0 22px 60px rgba(15,23,42,0.22);">
            <div style="padding:36px 36px 28px;background:radial-gradient(circle at top right,#67e8f9 0%,#0ea5e9 35%,#082f49 100%);">
              <p style="margin:0 0 10px;color:#cffafe;font-size:13px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">Welcome to Majiscope</p>
              <h1 style="margin:0;color:#ffffff;font-size:30px;line-height:1.2;">{escape(title)}</h1>
              <p style="margin:14px 0 0;color:#e0f2fe;font-size:15px;line-height:1.7;">{intro}</p>
            </div>
            <div style="padding:32px 36px 12px;">{body_html}</div>
            <div style="padding:0 36px 30px;">
              <div style="padding-top:18px;border-top:1px solid #e2e8f0;color:#64748b;font-size:12px;line-height:1.7;">
                {footer}
              </div>
            </div>
          </td>
        </tr>
      </table>
    </div>
    """


def send_account_invitation_email(
    *,
    recipient_email: str,
    role_label: str,
    assignment_lines: list[str],
    invite_url: str,
) -> InviteDeliveryResult:
    subject = "Complete your Majiscope account setup"
    safe_assignments = _render_detail_cards(assignment_lines)
    safe_invite_url = escape(invite_url)
    html_body = _wrap_email_html(
        badge="Majiscope Access Invitation",
        title=f"Finish setting up your {role_label} account",
        intro=(
            "You have been invited to join the Majiscope operations platform. "
            "Use the secure button below to create your password and activate your login."
        ),
        body_html=f"""
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom:18px;">
          {safe_assignments}
        </table>
        <div style="margin:0 0 24px;padding:18px 20px;border-radius:18px;background:#f8fafc;border:1px solid #e2e8f0;">
          <p style="margin:0 0 8px;color:#0f172a;font-size:15px;font-weight:700;">Activate your account</p>
          <p style="margin:0;color:#475569;font-size:14px;line-height:1.7;">
            This link is unique to you and expires automatically for security. Once completed, you can sign in to Majiscope immediately.
          </p>
        </div>
        <p style="margin:0 0 26px;">
          <a href="{safe_invite_url}" style="display:inline-block;padding:15px 24px;border-radius:14px;background:linear-gradient(135deg,#14b8a6 0%,#0891b2 100%);color:#ffffff;text-decoration:none;font-size:15px;font-weight:700;">
            Complete account setup
          </a>
        </p>
        <p style="margin:0 0 8px;color:#0f172a;font-size:13px;font-weight:700;">Button not opening?</p>
        <p style="margin:0 0 18px;color:#475569;font-size:13px;line-height:1.7;word-break:break-word;">
          Copy and paste this secure link into your browser:<br />
          <a href="{safe_invite_url}" style="color:#0891b2;text-decoration:underline;">{safe_invite_url}</a>
        </p>
        """,
        footer="If you were not expecting this email, you can safely ignore it. This mailbox is used for secure account access only.",
    )
    text_body = (
        f"Majiscope account invitation\n\n"
        f"You have been invited to Majiscope as a {role_label}.\n"
        + ("\n".join(assignment_lines) + "\n\n" if assignment_lines else "\n")
        + f"Complete your account setup here:\n{invite_url}\n\n"
        + "This link expires automatically for security.\n"
    )

    fallback_message: Optional[str] = None

    resend_result = _send_via_resend(
        recipient_email=recipient_email,
        subject=subject,
        html_body=html_body,
    )
    if resend_result and resend_result.method == "email":
        return resend_result
    if resend_result and resend_result.message:
        fallback_message = resend_result.message

    smtp_result = _send_via_smtp(
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
    if smtp_result and smtp_result.method == "email":
        return smtp_result
    if smtp_result and smtp_result.message:
        fallback_message = smtp_result.message

    return InviteDeliveryResult(
        method="manual_link",
        message=fallback_message or "No outbound email provider is configured. Share the invite link manually.",
        invite_url=invite_url,
    )


def send_engineer_invitation_email(
    *,
    recipient_email: str,
    role: str,
    team_name: str,
    dma_name: str,
    invite_url: str,
) -> InviteDeliveryResult:
    role_label = "Team Leader" if role == "team_leader" else "Engineer"
    return send_account_invitation_email(
        recipient_email=recipient_email,
        role_label=role_label,
        assignment_lines=[f"DMA: {dma_name}", f"Team: {team_name}"],
        invite_url=invite_url,
    )


def send_password_reset_email(
    *,
    recipient_email: str,
    role_label: str,
    reset_url: str,
) -> InviteDeliveryResult:
    subject = "Reset your Majiscope password"
    safe_reset_url = escape(reset_url)
    html_body = _wrap_email_html(
        badge="Majiscope Password Reset",
        title="Reset your Majiscope password",
        intro=(
            f"We received a password reset request for your <strong>{escape(role_label)}</strong> "
            "account. Use the secure button below to choose a new password."
        ),
        body_html=f"""
        <div style="margin:0 0 24px;padding:18px 20px;border-radius:18px;background:#f8fafc;border:1px solid #e2e8f0;">
          <p style="margin:0 0 8px;color:#0f172a;font-size:15px;font-weight:700;">Secure reset link</p>
          <p style="margin:0;color:#475569;font-size:14px;line-height:1.7;">
            This link expires automatically to help protect your account.
          </p>
        </div>
        <p style="margin:0 0 26px;">
          <a href="{safe_reset_url}" style="display:inline-block;padding:15px 24px;border-radius:14px;background:linear-gradient(135deg,#14b8a6 0%,#0891b2 100%);color:#ffffff;text-decoration:none;font-size:15px;font-weight:700;">
            Reset password
          </a>
        </p>
        <p style="margin:0 0 8px;color:#0f172a;font-size:13px;font-weight:700;">Button not opening?</p>
        <p style="margin:0 0 18px;color:#475569;font-size:13px;line-height:1.7;word-break:break-word;">
          Copy and paste this secure link into your browser:<br />
          <a href="{safe_reset_url}" style="color:#0891b2;text-decoration:underline;">{safe_reset_url}</a>
        </p>
        """,
        footer="If you did not request this password reset, you can safely ignore this email and your account will remain unchanged.",
    )
    text_body = (
        f"Majiscope password reset\n\n"
        f"We received a password reset request for your Majiscope {role_label} account.\n\n"
        f"Reset your password here:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email.\n"
    )

    fallback_message: Optional[str] = None

    resend_result = _send_via_resend(
        recipient_email=recipient_email,
        subject=subject,
        html_body=html_body,
    )
    if resend_result and resend_result.method == "email":
        return resend_result
    if resend_result and resend_result.message:
        fallback_message = resend_result.message

    smtp_result = _send_via_smtp(
        recipient_email=recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
    if smtp_result and smtp_result.method == "email":
        return smtp_result
    if smtp_result and smtp_result.message:
        fallback_message = smtp_result.message

    return InviteDeliveryResult(
        method="manual_link",
        message=fallback_message or "No outbound email provider is configured. Share the password reset link manually.",
        invite_url=reset_url,
    )


def _send_via_resend(*, recipient_email: str, subject: str, html_body: str) -> Optional[InviteDeliveryResult]:
    if not settings.resend_api_key or not settings.resend_from_email:
        return None

    payload = {
        "from": _format_sender(settings.resend_from_email, settings.resend_from_name),
        "to": [recipient_email],
        "subject": subject,
        "html": html_body,
    }

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20.0,
        )
        response.raise_for_status()
        return InviteDeliveryResult(
            method="email",
            message="Invitation email sent successfully.",
        )
    except Exception as exc:
        return InviteDeliveryResult(
            method="manual_link",
            message=f"Email API delivery failed, so a manual invite link was generated instead: {exc}",
        )


def _send_via_smtp(
    *,
    recipient_email: str,
    subject: str,
    text_body: str,
    html_body: str,
) -> Optional[InviteDeliveryResult]:
    if not settings.smtp_host or not settings.smtp_from_email:
        return None

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = _format_sender(settings.smtp_from_email, settings.smtp_from_name)
    message["To"] = recipient_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)

        return InviteDeliveryResult(
            method="email",
            message="Invitation email sent successfully.",
        )
    except Exception as exc:
        return InviteDeliveryResult(
            method="manual_link",
            message=f"SMTP delivery failed, so a manual invite link was generated instead: {exc}",
        )


def _format_sender(email: str, name: str) -> str:
    clean_name = (name or "").strip()
    return f"{clean_name} <{email}>" if clean_name else email
