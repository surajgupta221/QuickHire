import os
import resend
from config import settings

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via Resend"""
    try:
        resend_key = os.getenv("RESEND_API_KEY")
        if not resend_key:
            print(f"⚠️ Resend not configured")
            return False

        resend.api_key = resend_key

        params = {
            "from": "QuickHire <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }

        email = resend.Emails.send(params)
        print(f"✅ Email sent to {to_email}: {email}", flush=True)
        return True

    except Exception as e:
        print(f"❌ Email failed: {e}", flush=True)
        return False


def send_password_reset_email(to_email: str, reset_token: str, full_name: str):
    reset_url = f"https://quick-hire-yzwt.vercel.app/reset-password?token={reset_token}&email={to_email}"
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#1B4F9E;padding:20px;text-align:center;">
            <h1 style="color:white;margin:0;">⚡ QuickHire</h1>
        </div>
        <div style="padding:30px;background:white;">
            <h2>Hi {full_name},</h2>
            <p>Click the button below to reset your password.</p>
            <p>This link expires in <strong>1 hour</strong>.</p>
            <div style="text-align:center;margin:30px 0;">
                <a href="{reset_url}"
                   style="background:#1B4F9E;color:white;padding:15px 30px;
                          text-decoration:none;border-radius:8px;font-weight:bold;
                          display:inline-block;">
                    Reset My Password
                </a>
            </div>
            <p style="color:#999;font-size:13px;">
                If you didn't request this, ignore this email.
            </p>
        </div>
        <div style="background:#f5f5f5;padding:15px;text-align:center;
                    color:#999;font-size:12px;">
            © 2026 QuickHire
        </div>
    </div>
    """
    return send_email(to_email, "Reset Your QuickHire Password 🔑", html_body)


def send_welcome_email(to_email: str, full_name: str):
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#1B4F9E;padding:20px;text-align:center;">
            <h1 style="color:white;margin:0;">⚡ QuickHire</h1>
        </div>
        <div style="padding:30px;background:white;">
            <h2>Welcome, {full_name}! 🎉</h2>
            <p>Your account is ready with
               <strong>10 free screening credits!</strong>
            </p>
            <ul style="line-height:2;">
                <li>✅ Upload Job Descriptions</li>
                <li>✅ Screen up to 20 resumes</li>
                <li>✅ AI scores 0-100</li>
                <li>✅ Excel export</li>
            </ul>
            <div style="text-align:center;margin:30px 0;">
                <a href="https://quick-hire-yzwt.vercel.app"
                   style="background:#1B4F9E;color:white;padding:15px 30px;
                          text-decoration:none;border-radius:8px;font-weight:bold;
                          display:inline-block;">
                    Start Screening Now 🚀
                </a>
            </div>
        </div>
    </div>
    """
    return send_email(to_email, "Welcome to QuickHire! 🚀", html_body)