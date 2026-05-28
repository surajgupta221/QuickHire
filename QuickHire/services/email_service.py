import os
import resend
from config import settings

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    try:
        api_key = os.getenv("RESEND_API_KEY", "")
        if not api_key:
            print("⚠️ RESEND_API_KEY not configured", flush=True)
            return False

        resend.api_key = api_key

        # Resend free tier: from must be onboarding@resend.dev
        # and can only send to your own verified email
        params = {
            "from": "QuickHire <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }

        response = resend.Emails.send(params)
        print(f"✅ Email sent to {to_email}: {response}", flush=True)
        return True

    except Exception as e:
        print(f"❌ Resend failed: {e}", flush=True)
        return False


def send_password_reset_email(to_email: str, reset_token: str, full_name: str):
    # Use production URL for reset link
    reset_url = (
        f"https://quick-hire-lime.vercel.app/reset-password"
        f"?token={reset_token}&email={to_email}"
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#1B4F9E;padding:20px;text-align:center;">
            <h1 style="color:white;margin:0;">⚡ QuickHire</h1>
        </div>
        <div style="padding:30px;background:white;">
            <h2>Hi {full_name},</h2>
            <p>We received a request to reset your QuickHire password.</p>
            <p>Click the button below. This link expires in <strong>1 hour</strong>.</p>
            <div style="text-align:center;margin:30px 0;">
                <a href="{reset_url}"
                   style="background:#1B4F9E;color:white;padding:15px 30px;
                          text-decoration:none;border-radius:8px;font-weight:bold;
                          display:inline-block;">
                    Reset My Password
                </a>
            </div>
            <p style="color:#999;font-size:13px;">
                If button doesn't work, copy this link:<br/>
                <a href="{reset_url}">{reset_url}</a>
            </p>
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
            <p>Your account is ready with <strong>10 free screening credits!</strong></p>
            <ul style="line-height:2;">
                <li>✅ Upload Job Descriptions</li>
                <li>✅ Screen up to 20 resumes at once</li>
                <li>✅ AI scores 0-100 for each candidate</li>
                <li>✅ Export results to Excel</li>
            </ul>
            <div style="text-align:center;margin:30px 0;">
                <a href="https://quick-hire-lime.vercel.app"
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