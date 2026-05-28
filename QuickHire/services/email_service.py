import os
import resend
from config import settings

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via Resend using verified domain thequickhire.in"""
    try:
        api_key = os.getenv("RESEND_API_KEY", "")
        if not api_key:
            print("⚠️ RESEND_API_KEY not configured", flush=True)
            return False

        resend.api_key = api_key

        # Verified subdomain sender routing configuration
        from_address = "QuickHire <noreply@send.thequickhire.in>"

        params: resend.Emails.SendParams = {
            "from": from_address,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }

        response = resend.Emails.send(params)
        print(f"✅ Email sent to {to_email} from {from_address}", flush=True)
        print(f"Response: {response}", flush=True)
        return True

    except Exception as e:
        print(f"❌ Resend failed: {e}", flush=True)
        print(f"Error type: {type(e).__name__}", flush=True)
        return False


def send_password_reset_email(to_email: str, reset_token: str, full_name: str):
    """Send password reset email mapped directly to staging layer"""
    reset_url = (
        f"https://thequickhire.in"
        f"?token={reset_token}&email={to_email}"
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #eee;border-radius:8px;overflow:hidden;">
        <div style="background:#1B4F9E;padding:25px 20px;text-align:center;">
            <h1 style="color:white;margin:0;font-size:28px;">⚡ QuickHire</h1>
            <p style="color:#a8c4ff;margin:5px 0 0;">AI-Powered Recruitment Assistant</p>
        </div>
        <div style="padding:35px 30px;background:white;">
            <h2 style="color:#1B4F9E;">Hi {full_name},</h2>
            <p style="color:#555;line-height:1.6;">
                We received a request to reset your QuickHire password.
                Click the button below to create a new password.
            </p>
            <p style="color:#555;">This link expires in <strong>1 hour</strong>.</p>
            <div style="text-align:center;margin:35px 0;">
                <a href="{reset_url}"
                   style="background:#1B4F9E;color:white;padding:15px 35px;
                          text-decoration:none;border-radius:8px;font-weight:bold;
                          font-size:16px;display:inline-block;">
                    🔑 Reset My Password
                </a>
            </div>
            <p style="color:#999;font-size:13px;line-height:1.5;">
                If the button doesn't work, copy and paste this link:<br/>
                <a href="{reset_url}" style="color:#1B4F9E;">{reset_url}</a>
            </p>
            <hr style="border:none;border-top:1px solid #eee;margin:25px 0;">
            <p style="color:#999;font-size:12px;">
                If you didn't request a password reset, ignore this email.
                Your password won't change.
            </p>
        </div>
        <div style="background:#f8f9fa;padding:15px;text-align:center;
                    color:#999;font-size:12px;">
            © 2026 QuickHire — thequickhire.in
        </div>
    </div>
    """
    return send_email(to_email, "🔑 Reset Your QuickHire Password", html_body)


def send_welcome_email(to_email: str, full_name: str):
    """Send welcome email on registration"""
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #eee;border-radius:8px;overflow:hidden;">
        <div style="background:#1B4F9E;padding:25px 20px;text-align:center;">
            <h1 style="color:white;margin:0;font-size:28px;">⚡ QuickHire</h1>
            <p style="color:#a8c4ff;margin:5px 0 0;">AI-Powered Recruitment Assistant</p>
        </div>
        <div style="padding:35px 30px;background:white;">
            <h2 style="color:#1B4F9E;">Welcome, {full_name}! 🎉</h2>
            <p style="color:#555;line-height:1.6;">
                Your QuickHire account is ready with
                <strong>10 free screening credits!</strong>
            </p>
            <h3 style="color:#333;">What you can do:</h3>
            <ul style="color:#555;line-height:2.2;">
                <li>✅ Upload Job Descriptions (PDF/Word/Excel)</li>
                <li>✅ Screen up to 20 resumes at once</li>
                <li>✅ Get AI scores 0-100 for each candidate</li>
                <li>✅ Download results as Excel</li>
                <li>✅ Auto-generated interview questions</li>
            </ul>
            <div style="text-align:center;margin:35px 0;">
                <a href="https://thequickhire.in"
                   style="background:#1B4F9E;color:white;padding:15px 35px;
                          text-decoration:none;border-radius:8px;font-weight:bold;
                          font-size:16px;display:inline-block;">
                    🚀 Start Screening Now
                </a>
            </div>
        </div>
        <div style="background:#f8f9fa;padding:15px;text-align:center;
                    color:#999;font-size:12px;">
            © 2026 QuickHire — thequickhire.in
        </div>
    </div>
    """
    return send_email(to_email, "🎉 Welcome to QuickHire!", html_body)
