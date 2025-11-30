"""
Payment API routes for credits and premium subscriptions.
Supports Ozow (web), Google Play IAP, and Apple IAP.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional, List
from datetime import datetime, timedelta
import secrets

from app.database import get_session
from app.api.deps import get_current_user
from app.models.profile import Profile
from app.models.payment import (
    Payment, 
    Subscription, 
    CreditPackage, 
    PremiumPlan,
    PaymentProvider,
    PaymentStatus,
    PaymentType
)
from app.models.credit import CreditBalance, CreditTransaction, TransactionType
from app.services.ozow_payment import ozow_service
from app.services.iap_service import iap_service
from app.services.credit_service import CreditService
from app.schemas.payment import (
    CreditPackageResponse,
    PremiumPlanResponse,
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentWebhookData,
    IAPVerifyRequest,
    SubscriptionResponse
)

router = APIRouter(prefix="/payments", tags=["payments"])


# ==================== Credit Packages ====================

@router.get("/credit-packages", response_model=List[CreditPackageResponse])
async def get_credit_packages(
    session: AsyncSession = Depends(get_session)
):
    """
    Get available credit packages for purchase.
    """
    result = await session.execute(
        select(CreditPackage)
        .where(CreditPackage.is_active == True)
        .order_by(CreditPackage.display_order)
    )
    packages = result.scalars().all()
    
    return [CreditPackageResponse.from_orm(p) for p in packages]


@router.get("/premium-plans", response_model=List[PremiumPlanResponse])
async def get_premium_plans(
    session: AsyncSession = Depends(get_session)
):
    """
    Get available premium subscription plans.
    """
    result = await session.execute(
        select(PremiumPlan)
        .where(PremiumPlan.is_active == True)
        .order_by(PremiumPlan.display_order)
    )
    plans = result.scalars().all()
    
    return [PremiumPlanResponse.from_orm(p) for p in plans]


# ==================== Ozow Payments (Web) ====================

@router.post("/ozow/initiate", response_model=PaymentInitiateResponse)
async def initiate_ozow_payment(
    request: PaymentInitiateRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Initiate an Ozow payment for credits or premium subscription.
    Returns payment URL and data for Next.js frontend.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get package or plan details
    amount = 0
    credits_amount = None
    payment_type = None
    
    if request.credit_package_id:
        result = await session.execute(
            select(CreditPackage).where(CreditPackage.id == request.credit_package_id)
        )
        package = result.scalar_one_or_none()
        if not package:
            raise HTTPException(status_code=404, detail="Credit package not found")
        
        amount = package.price
        credits_amount = package.credits + package.bonus_credits
        payment_type = PaymentType.CREDITS
    
    elif request.premium_plan_id:
        result = await session.execute(
            select(PremiumPlan).where(PremiumPlan.id == request.premium_plan_id)
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise HTTPException(status_code=404, detail="Premium plan not found")
        
        amount = plan.price
        payment_type = plan.plan_type
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Either credit_package_id or premium_plan_id is required"
        )
    
    # Generate unique transaction reference
    transaction_ref = f"WDD-{profile.id}-{secrets.token_hex(8)}"
    
    # Create payment record
    payment = Payment(
        profile_id=profile.id,
        payment_type=payment_type,
        payment_provider=PaymentProvider.OZOW,
        amount=amount,
        credits_amount=credits_amount,
        status=PaymentStatus.PENDING
    )
    
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    
    # Create Ozow payment request
    payment_request = ozow_service.create_payment_request(
        transaction_reference=transaction_ref,
        amount=amount,
        customer_email=current_user.get("email", ""),
        customer_name=profile.display_name or "User",
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        error_url=request.error_url,
        notify_url=request.notify_url,
        optional_fields={
            "Optional1": str(payment.id),  # Store payment ID for webhook
            "Optional2": str(profile.id),
            "Optional3": payment_type.value
        }
    )
    
    # Update payment with Ozow transaction reference
    payment.ozow_transaction_id = transaction_ref
    await session.commit()
    
    return PaymentInitiateResponse(
        payment_id=payment.id,
        payment_url=payment_request["payment_url"],
        payment_data=payment_request["payment_data"],
        transaction_reference=transaction_ref
    )


@router.post("/ozow/webhook")
async def ozow_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """
    Webhook endpoint for Ozow payment notifications.
    Called by Ozow when payment status changes.
    """
    # Get form data
    form_data = await request.form()
    webhook_data = dict(form_data)
    
    # Verify webhook hash
    if not ozow_service.verify_webhook_hash(webhook_data):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    # Get payment ID from Optional1
    payment_id = webhook_data.get("Optional1")
    if not payment_id:
        raise HTTPException(status_code=400, detail="Payment ID not found")
    
    # Get payment record
    result = await session.execute(
        select(Payment).where(Payment.id == int(payment_id))
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Update payment status
    status = webhook_data.get("Status", "").lower()
    
    if status == "complete":
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()
        
        # Process payment in background
        background_tasks.add_task(
            process_completed_payment,
            payment.id,
            session
        )
    
    elif status == "cancelled":
        payment.status = PaymentStatus.CANCELLED
    
    elif status == "error":
        payment.status = PaymentStatus.FAILED
        payment.status_message = webhook_data.get("StatusMessage", "")
    
    payment.ozow_transaction_id = webhook_data.get("TransactionId")
    
    await session.commit()
    
    return {"status": "success"}


# ==================== IAP Payments (Mobile) ====================

@router.post("/iap/verify-google-play")
async def verify_google_play_purchase(
    request: IAPVerifyRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """
    Verify a Google Play In-App Purchase.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Verify purchase with Google Play
    is_subscription = request.payment_type in [
        PaymentType.PREMIUM_MONTHLY,
        PaymentType.PREMIUM_YEARLY
    ]
    
    purchase_data = await iap_service.verify_google_play_purchase(
        product_id=request.product_id,
        purchase_token=request.purchase_token,
        is_subscription=is_subscription
    )
    
    if not purchase_data:
        raise HTTPException(status_code=400, detail="Invalid purchase")
    
    # Check if purchase is valid
    purchase_state = purchase_data.get("purchaseState")
    if purchase_state != 0:  # 0 = Purchased
        raise HTTPException(status_code=400, detail="Purchase not completed")
    
    # Create payment record
    payment = Payment(
        profile_id=profile.id,
        payment_type=request.payment_type,
        payment_provider=PaymentProvider.GOOGLE_PLAY,
        amount=0,  # Amount not available from Google Play API
        google_play_order_id=purchase_data.get("orderId"),
        google_play_purchase_token=request.purchase_token,
        status=PaymentStatus.COMPLETED,
        completed_at=datetime.utcnow()
    )
    
    # Set credits amount if applicable
    if request.credits_amount:
        payment.credits_amount = request.credits_amount
    
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    
    # Acknowledge purchase
    background_tasks.add_task(
        iap_service.acknowledge_google_play_purchase,
        request.product_id,
        request.purchase_token
    )
    
    # Process payment
    background_tasks.add_task(
        process_completed_payment,
        payment.id,
        session
    )
    
    return {"status": "success", "payment_id": payment.id}


@router.post("/iap/verify-apple")
async def verify_apple_purchase(
    request: IAPVerifyRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """
    Verify an Apple In-App Purchase.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Verify receipt with Apple
    purchase_data = await iap_service.verify_apple_purchase(request.receipt_data)
    
    if not purchase_data:
        raise HTTPException(status_code=400, detail="Invalid receipt")
    
    # Create payment record
    payment = Payment(
        profile_id=profile.id,
        payment_type=request.payment_type,
        payment_provider=PaymentProvider.APPLE_IAP,
        amount=0,  # Amount not available from Apple
        apple_transaction_id=purchase_data.get("transaction_id"),
        apple_receipt_data=request.receipt_data,
        status=PaymentStatus.COMPLETED,
        completed_at=datetime.utcnow()
    )
    
    # Set credits amount if applicable
    if request.credits_amount:
        payment.credits_amount = request.credits_amount
    
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    
    # Process payment
    background_tasks.add_task(
        process_completed_payment,
        payment.id,
        session
    )
    
    return {"status": "success", "payment_id": payment.id}


# ==================== Subscription Management ====================

@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_subscription(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get user's current premium subscription.
    """
    # Get user's profile
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Get subscription
    result = await session.execute(
        select(Subscription).where(Subscription.profile_id == profile.id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        return None
    
    return SubscriptionResponse.from_orm(subscription)


# ==================== Helper Functions ====================

async def process_completed_payment(payment_id: int, session: AsyncSession):
    """
    Process a completed payment (add credits or activate premium).
    """
    # Get payment
    result = await session.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment or payment.status != PaymentStatus.COMPLETED:
        return
    
    # Get profile
    result = await session.execute(
        select(Profile).where(Profile.id == payment.profile_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        return
    
    # Process based on payment type
    if payment.payment_type == PaymentType.CREDITS:
        # Add credits
        credit_service = CreditService()
        await credit_service.add_credits(
            profile_id=profile.id,
            amount=payment.credits_amount,
            transaction_type=TransactionType.PURCHASE,
            description=f"Credit purchase - Payment #{payment.id}",
            session=session
        )
    
    elif payment.payment_type in [
        PaymentType.PREMIUM_DAILY,
        PaymentType.PREMIUM_WEEKLY,
        PaymentType.PREMIUM_MONTHLY,
        PaymentType.PREMIUM_YEARLY
    ]:
        # Activate premium subscription
        if payment.payment_type == PaymentType.PREMIUM_DAILY:
            duration_days = 1
        elif payment.payment_type == PaymentType.PREMIUM_WEEKLY:
            duration_days = 7
        elif payment.payment_type == PaymentType.PREMIUM_MONTHLY:
            duration_days = 30
        else:  # YEARLY
            duration_days = 365
            
        expires_at = datetime.utcnow() + timedelta(days=duration_days)
        
        # Check if subscription exists
        result = await session.execute(
            select(Subscription).where(Subscription.profile_id == profile.id)
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            # Update existing
            subscription.plan_type = payment.payment_type
            subscription.payment_provider = payment.payment_provider
            subscription.is_active = True
            subscription.expires_at = expires_at
            subscription.last_payment_id = payment.id
            subscription.updated_at = datetime.utcnow()
        else:
            # Create new
            subscription = Subscription(
                profile_id=profile.id,
                plan_type=payment.payment_type,
                payment_provider=payment.payment_provider,
                is_active=True,
                expires_at=expires_at,
                last_payment_id=payment.id
            )
            session.add(subscription)
        
        # Update profile premium status
        profile.is_premium = True
        
        await session.commit()
