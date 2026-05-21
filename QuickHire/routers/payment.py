from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.payment import Payment
from services.auth import verify_token, get_user_by_email
from dotenv import load_dotenv
from config import settings
import razorpay
import hashlib
import hmac
import os

load_dotenv()

router = APIRouter(prefix="/payment", tags=["Payment"])

# ─── Razorpay Client ──────────────────────────
client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

PLANS = {
    "pay_per_use": {
        "amount": settings.PAY_PER_USE_AMOUNT,
        "credits": settings.PAY_PER_USE_CREDITS,
        "name": "Pay Per Use",
        "description": "1 screening credit"
    },
    "monthly": {
        "amount": settings.MONTHLY_AMOUNT,
        "credits": settings.MONTHLY_CREDITS,
        "name": "Monthly Plan",
        "description": "70 screenings for 1 month"
    },
    "annual": {
        "amount": settings.ANNUAL_AMOUNT,
        "credits": settings.ANNUAL_CREDITS,
        "name": "Annual Plan",
        "description": "850 screenings for 1 year"
    }
}


# ─── Create Order ─────────────────────────────
@router.post("/create-order")
def create_order(
    plan: str,
    token: str,
    db: Session = Depends(get_db)
):
    """Create a Razorpay payment order"""

    # Verify user
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_email(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate plan
    if plan not in PLANS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan. Choose from: {list(PLANS.keys())}"
        )

    plan_data = PLANS[plan]

    # Create Razorpay order
    try:
        order = client.order.create({
            "amount": plan_data["amount"],
            "currency": "INR",
            "notes": {
                "user_id": user.id,
                "plan": plan,
                "email": user.email
            }
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Payment gateway error: {str(e)}"
        )

    # Save order to database
    payment = Payment(
        user_id=user.id,
        razorpay_order_id=order["id"],
        plan=plan,
        amount=plan_data["amount"] / 100,
        credits_to_add=plan_data["credits"],
        status="pending"
    )
    db.add(payment)
    db.commit()

    return {
        "order_id": order["id"],
        "amount": plan_data["amount"],
        "currency": "INR",
        "plan": plan,
        "plan_name": plan_data["name"],
        "description": plan_data["description"],
        "razorpay_key": os.getenv("RAZORPAY_KEY_ID"),
        "user_name": user.full_name,
        "user_email": user.email,
        "user_phone": user.phone or ""
    }

# ─── Verify Payment ───────────────────────────
@router.post("/verify")
def verify_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    token: str,
    db: Session = Depends(get_db)
):
    """Verify payment and add credits to account"""

    # Verify user
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_email(db, payload.get("sub"))

    # Verify signature
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(
        key_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    if expected_signature != razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Payment verification failed — invalid signature"
        )

    # Find payment record
    payment = db.query(Payment).filter(
        Payment.razorpay_order_id == razorpay_order_id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    # Update payment record
    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = "completed"

    # Add credits to user
    user.screening_credits += payment.credits_to_add
    user.plan = payment.plan

    db.commit()

    return {
        "message": "Payment successful!",
        "plan": payment.plan,
        "credits_added": payment.credits_to_add,
        "new_credit_balance": user.screening_credits
    }

# ─── Payment History ──────────────────────────
@router.get("/history")
def payment_history(token: str, db: Session = Depends(get_db)):
    """Get payment history for current user"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_email(db, payload.get("sub"))

    payments = db.query(Payment).filter(
        Payment.user_id == user.id
    ).order_by(Payment.created_at.desc()).all()

    return {
        "total": len(payments),
        "payments": [
            {
                "id": p.id,
                "plan": p.plan,
                "amount": p.amount,
                "credits": p.credits_to_add,
                "status": p.status,
                "date": p.created_at
            }
            for p in payments
        ]
    }

# ─── Get Plans ────────────────────────────────
@router.get("/plans")
def get_plans():
    """Get all available plans"""
    return {
        "plans": [
            {
                "id": key,
                "name": val["name"],
                "amount": val["amount"] / 100,
                "credits": val["credits"],
                "description": val["description"]
            }
            for key, val in PLANS.items()
        ]
    }