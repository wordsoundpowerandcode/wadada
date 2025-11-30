"""
In-App Purchase (IAP) service for Flutter mobile app.
Handles Google Play and Apple App Store purchases.
"""
from typing import Dict, Optional
import httpx
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from google.auth.transport.requests import Request

from app.config import settings


class GooglePlayIAPService:
    """
    Service for verifying Google Play In-App Purchases.
    Uses Google Play Developer API.
    """
    
    def __init__(self):
        self.package_name = settings.GOOGLE_PLAY_PACKAGE_NAME
        self.service_account_file = settings.GOOGLE_PLAY_SERVICE_ACCOUNT_FILE
        
        # Initialize credentials
        if self.service_account_file:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/androidpublisher']
            )
        else:
            self.credentials = None
    
    async def verify_purchase(
        self,
        product_id: str,
        purchase_token: str
    ) -> Optional[Dict]:
        """
        Verify a one-time product purchase (credits).
        """
        if not self.credentials:
            return None
        
        # Refresh credentials if needed
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        
        url = (
            f"https://androidpublisher.googleapis.com/androidpublisher/v3"
            f"/applications/{self.package_name}"
            f"/purchases/products/{product_id}"
            f"/tokens/{purchase_token}"
        )
        
        headers = {
            "Authorization": f"Bearer {self.credentials.token}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error verifying Google Play purchase: {e}")
            return None
    
    async def verify_subscription(
        self,
        subscription_id: str,
        purchase_token: str
    ) -> Optional[Dict]:
        """
        Verify a subscription purchase (premium).
        """
        if not self.credentials:
            return None
        
        # Refresh credentials if needed
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        
        url = (
            f"https://androidpublisher.googleapis.com/androidpublisher/v3"
            f"/applications/{self.package_name}"
            f"/purchases/subscriptions/{subscription_id}"
            f"/tokens/{purchase_token}"
        )
        
        headers = {
            "Authorization": f"Bearer {self.credentials.token}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error verifying Google Play subscription: {e}")
            return None
    
    async def acknowledge_purchase(
        self,
        product_id: str,
        purchase_token: str
    ) -> bool:
        """
        Acknowledge a purchase (required by Google Play).
        """
        if not self.credentials:
            return False
        
        # Refresh credentials if needed
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        
        url = (
            f"https://androidpublisher.googleapis.com/androidpublisher/v3"
            f"/applications/{self.package_name}"
            f"/purchases/products/{product_id}"
            f"/tokens/{purchase_token}:acknowledge"
        )
        
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json={})
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error acknowledging Google Play purchase: {e}")
            return False


class AppleIAPService:
    """
    Service for verifying Apple App Store In-App Purchases.
    Uses App Store Server API.
    """
    
    def __init__(self):
        self.shared_secret = settings.APPLE_SHARED_SECRET
        self.bundle_id = settings.APPLE_BUNDLE_ID
        
        # URLs
        self.sandbox_url = "https://sandbox.itunes.apple.com/verifyReceipt"
        self.production_url = "https://buy.itunes.apple.com/verifyReceipt"
    
    async def verify_receipt(
        self,
        receipt_data: str,
        is_sandbox: bool = False
    ) -> Optional[Dict]:
        """
        Verify an Apple receipt.
        Works for both one-time purchases and subscriptions.
        """
        url = self.sandbox_url if is_sandbox else self.production_url
        
        payload = {
            "receipt-data": receipt_data,
            "password": self.shared_secret,
            "exclude-old-transactions": True
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # If status is 21007, receipt is from sandbox but sent to production
                # Retry with sandbox URL
                if data.get("status") == 21007 and not is_sandbox:
                    return await self.verify_receipt(receipt_data, is_sandbox=True)
                
                return data
        except Exception as e:
            print(f"Error verifying Apple receipt: {e}")
            return None
    
    def parse_receipt_data(self, receipt_response: Dict) -> Optional[Dict]:
        """
        Parse Apple receipt response to extract purchase info.
        """
        if receipt_response.get("status") != 0:
            return None
        
        receipt = receipt_response.get("receipt", {})
        latest_receipt_info = receipt_response.get("latest_receipt_info", [])
        
        # For subscriptions, get the latest info
        if latest_receipt_info:
            latest = latest_receipt_info[-1]
            return {
                "product_id": latest.get("product_id"),
                "transaction_id": latest.get("transaction_id"),
                "original_transaction_id": latest.get("original_transaction_id"),
                "purchase_date": latest.get("purchase_date_ms"),
                "expires_date": latest.get("expires_date_ms"),
                "is_trial": latest.get("is_trial_period") == "true",
                "is_subscription": True
            }
        
        # For one-time purchases
        in_app = receipt.get("in_app", [])
        if in_app:
            purchase = in_app[-1]
            return {
                "product_id": purchase.get("product_id"),
                "transaction_id": purchase.get("transaction_id"),
                "original_transaction_id": purchase.get("original_transaction_id"),
                "purchase_date": purchase.get("purchase_date_ms"),
                "is_subscription": False
            }
        
        return None


class IAPService:
    """
    Unified IAP service that handles both Google Play and Apple.
    """
    
    def __init__(self):
        self.google_play = GooglePlayIAPService()
        self.apple = AppleIAPService()
    
    async def verify_google_play_purchase(
        self,
        product_id: str,
        purchase_token: str,
        is_subscription: bool = False
    ) -> Optional[Dict]:
        """Verify Google Play purchase."""
        if is_subscription:
            return await self.google_play.verify_subscription(product_id, purchase_token)
        else:
            return await self.google_play.verify_purchase(product_id, purchase_token)
    
    async def verify_apple_purchase(
        self,
        receipt_data: str
    ) -> Optional[Dict]:
        """Verify Apple purchase."""
        receipt_response = await self.apple.verify_receipt(receipt_data)
        if receipt_response:
            return self.apple.parse_receipt_data(receipt_response)
        return None
    
    async def acknowledge_google_play_purchase(
        self,
        product_id: str,
        purchase_token: str
    ) -> bool:
        """Acknowledge Google Play purchase."""
        return await self.google_play.acknowledge_purchase(product_id, purchase_token)


# Singleton instance
iap_service = IAPService()
