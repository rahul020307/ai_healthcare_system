import os
import smtplib
import datetime
from email.message import EmailMessage
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def _get_smtp_config():
    load_dotenv()
    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com").strip() if (os.getenv("SMTP_USER") or os.getenv("SMTP_HOST")) else "",
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", "").strip(),
        "pass": os.getenv("SMTP_PASS", "").strip().replace(" ", ""),
        "from": os.getenv("SMTP_FROM", "").strip() or f"CuraAssist Security <{os.getenv('SMTP_USER', 'security@curaassist.health')}>",
        "use_ssl": os.getenv("SMTP_USE_SSL", "false").lower() in ["true", "1", "yes"] or os.getenv("SMTP_PORT") == "465",
    }


def send_security_login_email(
    recipient_email: str,
    user_name: str = "User",
    ip_address: str = "127.0.0.1",
    user_agent: str = "Web Browser",
    timestamp: Optional[str] = None,
) -> bool:
    """Send an automated security alert email to the user notifying them of a new login."""
    if not recipient_email or "@" not in recipient_email:
        print("[EmailService] Invalid recipient email:", recipient_email)
        return False

    if not timestamp:
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    subject = "🔒 Security Alert: New Sign-in to your CuraAssist Account"
    
    # Plain text version
    text_content = f"""Hello {user_name},

Your CuraAssist Healthcare account ({recipient_email}) was just logged into from a new session.

Login Details:
• Time (UTC): {timestamp}
• Device / Browser: {user_agent}
• IP Address: {ip_address}

Was this not you?
If you did not initiate this login, your credentials may be compromised. Please reset your password immediately and contact CuraAssist Support.

—
CuraAssist CareHub Automated Security System
"""

    # HTML formatted version
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b1120; color: #f8fafc; padding: 24px; margin: 0;">
  <div style="max-width: 580px; margin: 0 auto; background: #1e293b; border-radius: 16px; border: 1px solid #334155; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
    <div style="text-align: center; margin-bottom: 24px;">
      <span style="font-size: 26px; font-weight: 800; color: #38bdf8;">CuraAssist CareHub</span>
      <p style="color: #94a3b8; font-size: 13px; margin: 4px 0 0 0;">Smart AI Healthcare & Medical Network</p>
    </div>
    
    <div style="border-top: 1px solid #334155; padding-top: 20px;">
      <h2 style="color: #38bdf8; font-size: 18px; margin: 0 0 14px 0;">🔒 Security Alert: New Sign-in Detected</h2>
      <p style="font-size: 15px; color: #e2e8f0; line-height: 1.5; margin: 0 0 12px 0;">
        Hello <strong>{user_name}</strong>,
      </p>
      <p style="font-size: 14px; color: #cbd5e1; line-height: 1.6; margin: 0 0 20px 0;">
        Your CuraAssist account (<strong>{recipient_email}</strong>) was just accessed from a new device or session.
      </p>

      <div style="background: #0f172a; border-radius: 12px; border: 1px solid #334155; padding: 16px; margin: 20px 0;">
        <table style="width: 100%; font-size: 13px; color: #94a3b8; border-collapse: collapse;">
          <tr>
            <td style="padding: 6px 0; font-weight: 600; color: #e2e8f0; width: 40%;">⏰ Time:</td>
            <td style="padding: 6px 0; color: #38bdf8;">{timestamp}</td>
          </tr>
          <tr>
            <td style="padding: 6px 0; font-weight: 600; color: #e2e8f0;">📱 Device / Browser:</td>
            <td style="padding: 6px 0; color: #f1f5f9;">{user_agent}</td>
          </tr>
          <tr>
            <td style="padding: 6px 0; font-weight: 600; color: #e2e8f0;">🌐 IP Address:</td>
            <td style="padding: 6px 0; color: #f1f5f9;">{ip_address}</td>
          </tr>
        </table>
      </div>

      <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 12px; padding: 16px; margin-top: 24px;">
        <p style="color: #f87171; font-weight: 700; font-size: 14px; margin: 0 0 6px 0;">⚠️ Was this not you?</p>
        <p style="color: #cbd5e1; font-size: 13px; margin: 0; line-height: 1.5;">
          If you did not perform this login, your password may have been exposed. Please change your password immediately or reach out to CuraAssist Security Support.
        </p>
      </div>
    </div>

    <div style="text-align: center; margin-top: 32px; border-top: 1px solid #334155; padding-top: 16px; font-size: 12px; color: #64748b;">
      This is an automated security notification.<br>© 2026 CuraAssist Healthcare System. All rights reserved.
    </div>
  </div>
</body>
</html>
"""

    config = _get_smtp_config()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config["from"]
    msg["To"] = recipient_email
    msg.set_content(text_content)
    msg.add_alternative(html_content, subtype="html")

    # 1. If SMTP server is configured, deliver via SMTP
    if config["host"] and config["user"] and config["pass"]:
        try:
            if config["use_ssl"] or config["port"] == 465:
                with smtplib.SMTP_SSL(config["host"], config["port"], timeout=10) as server:
                    server.login(config["user"], config["pass"])
                    server.send_message(msg)
            else:
                with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
                    server.starttls()
                    server.login(config["user"], config["pass"])
                    server.send_message(msg)
            print(f"[EmailService] Security login email dispatched successfully to {recipient_email}")
            return True
        except Exception as exc:
            print(f"[EmailService] Failed to send email via SMTP ({config['host']}):", exc)
            return False

    # 2. Resilient fallback / Audit log
    print(f"[EmailService - Security Notification] Queued login alert for {recipient_email} at {timestamp} (Configure SMTP_USER & SMTP_PASS in .env to send live mail)")
    return True
