import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    try:
        if not settings.EMAIL_USERNAME or not settings.EMAIL_PASSWORD:
            print(f"Email not configured. Would send to {to_email}: {subject}")
            return False

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"QuickHire <{settings.EMAIL_USERNAME}>"
        msg['To'] = to_email

        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_USERNAME, to_email, msg.as_string())

        print(f"✅ Email sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Email failed: {e}")
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
            <p>Click below to reset your password. Link expires in 1 hour.</p>
            <div style="text-align:center;margin:30px 0;">
                <a href="{reset_url}"
                   style="background:#1B4F9E;color:white;padding:15px 30px;
                          text-decoration:none;border-radius:8px;font-weight:bold;">
                    Reset My Password
                </a>
            </div>
            <p style="color:#666;font-size:14px;">
                If you didn't request this, ignore this email.
            </p>
        </div>
    </div>
    """
    return send_email(to_email, "Reset Your QuickHire Password", html_body)


def send_welcome_email(to_email: str, full_name: str):
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <div style="background:#1B4F9E;padding:20px;text-align:center;">
            <h1 style="color:white;margin:0;">⚡ QuickHire</h1>
        </div>
        <div style="padding:30px;background:white;">
            <h2>Welcome, {full_name}! 🎉</h2>
            <p>Your QuickHire account is ready with <strong>10 free screening credits!</strong></p>
            <ul>
                <li>✅ Upload Job Descriptions (PDF/Word/Excel)</li>
                <li>✅ Screen up to 20 resumes at once</li>
                <li>✅ Get AI scores 0-100 for each candidate</li>
                <li>✅ Download results as Excel</li>
            </ul>
            <div style="text-align:center;margin:30px 0;">
                <a href="https://quick-hire-yzwt.vercel.app"
                   style="background:#1B4F9E;color:white;padding:15px 30px;
                          text-decoration:none;border-radius:8px;font-weight:bold;">
                    Start Screening Now
                </a>
            </div>
        </div>
    </div>
    """
    return send_email(to_email, "Welcome to QuickHire! 🚀", html_body)