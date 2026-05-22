import os
from dotenv import load_dotenv


# Load .env file
load_dotenv()

class Settings:
    # ─── App ──────────────────────────────────
    APP_NAME: str = os.getenv("APP_NAME", "QuickHire")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # ─── Database ─────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./quickhire.db")

    # ─── Security ─────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    ADMIN_KEY: str = os.getenv("ADMIN_KEY", "admin-key")

    # ─── Gemini AI ────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "YOUR_BACKUP_KEY_HERE")

    # ─── Razorpay ─────────────────────────────
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")

    # ─── Email ────────────────────────────────
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")

    # ─── Plans ────────────────────────────────
    FREE_CREDITS: int = int(os.getenv("FREE_CREDITS", 5))
    PAY_PER_USE_CREDITS: int = int(os.getenv("PAY_PER_USE_CREDITS", 1))
    MONTHLY_CREDITS: int = int(os.getenv("MONTHLY_CREDITS", 70))
    ANNUAL_CREDITS: int = int(os.getenv("ANNUAL_CREDITS", 850))

    PAY_PER_USE_AMOUNT: int = int(os.getenv("PAY_PER_USE_AMOUNT", 4900))
    MONTHLY_AMOUNT: int = int(os.getenv("MONTHLY_AMOUNT", 199900))
    ANNUAL_AMOUNT: int = int(os.getenv("ANNUAL_AMOUNT", 1999900))

# Single instance used everywhere
settings = Settings()