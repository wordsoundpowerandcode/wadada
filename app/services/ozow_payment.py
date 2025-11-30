"""
Ozow payment service for Next.js web app.
Handles payment initialization, webhooks, and verification.
"""
import hashlib
import hmac
from typing import Dict, Optional
from datetime import datetime
import httpx

from app.config import settings


class OzowPaymentService:
    """
    Service for integrating with Ozow payment gateway.
    Ozow is a popular South African payment provider.
    """
    
    def __init__(self):
        self.site_code = settings.OZOW_SITE_CODE
        self.private_key = settings.OZOW_PRIVATE_KEY
        self.api_key = settings.OZOW_API_KEY
        self.is_test_mode = settings.OZOW_TEST_MODE
        
        # URLs
        if self.is_test_mode:
            self.payment_url = "https://pay.ozow.com"
            self.api_url = "https://api.ozow.com"
        else:
            self.payment_url = "https://pay.ozow.com"
            self.api_url = "https://api.ozow.com"
    
    def generate_hash(self, data: Dict[str, str]) -> str:
        """
        Generate hash for Ozow payment request.
        Hash is used to verify payment integrity.
        """
        # Ozow hash format: SiteCode + TransactionReference + Amount + (Optional)CancelUrl + 
        # (Optional)ErrorUrl + (Optional)SuccessUrl + (Optional)NotifyUrl + IsTest + PrivateKey
        hash_string = (
            f"{data.get('SiteCode', '')}"
            f"{data.get('TransactionReference', '')}"
            f"{data.get('Amount', '')}"
            f"{data.get('CancelUrl', '')}"
            f"{data.get('ErrorUrl', '')}"
            f"{data.get('SuccessUrl', '')}"
            f"{data.get('NotifyUrl', '')}"
            f"{data.get('IsTest', 'false')}"
            f"{self.private_key}"
        )
        
        # Create SHA512 hash
        hash_bytes = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()
        return hash_bytes.lower()
    
    def create_payment_request(
        self,
        transaction_reference: str,
        amount: float,
        customer_email: str,
        customer_name: str,
        success_url: str,
        cancel_url: str,
        error_url: str,
        notify_url: str,
        optional_fields: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Create a payment request for Ozow.
        Returns a dictionary with payment URL and parameters.
        """
        # Format amount (Ozow expects amount in cents as string)
        amount_cents = str(int(amount * 100))
        
        # Build payment data
        payment_data = {
            "SiteCode": self.site_code,
            "TransactionReference": transaction_reference,
            "Amount": amount_cents,
            "CancelUrl": cancel_url,
            "ErrorUrl": error_url,
            "SuccessUrl": success_url,
            "NotifyUrl": notify_url,
            "IsTest": "true" if self.is_test_mode else "false",
            "Customer": customer_email,
            "BankReference": customer_name[:20],  # Max 20 chars
        }
        
        # Add optional fields
        if optional_fields:
            payment_data.update(optional_fields)
        
        # Generate hash
        payment_data["HashCheck"] = self.generate_hash(payment_data)
        
        return {
            "payment_url": self.payment_url,
            "payment_data": payment_data
        }
    
    def verify_webhook_hash(self, webhook_data: Dict[str, str]) -> bool:
        """
        Verify the hash from Ozow webhook notification.
        This ensures the webhook is genuinely from Ozow.
        """
        received_hash = webhook_data.get("HashCheck", "").lower()
        
        # Recreate hash from webhook data
        hash_string = (
            f"{webhook_data.get('SiteCode', '')}"
            f"{webhook_data.get('TransactionId', '')}"
            f"{webhook_data.get('TransactionReference', '')}"
            f"{webhook_data.get('Amount', '')}"
            f"{webhook_data.get('Status', '')}"
            f"{webhook_data.get('Optional1', '')}"
            f"{webhook_data.get('Optional2', '')}"
            f"{webhook_data.get('Optional3', '')}"
            f"{webhook_data.get('Optional4', '')}"
            f"{webhook_data.get('Optional5', '')}"
            f"{webhook_data.get('CurrencyCode', '')}"
            f"{webhook_data.get('IsTest', '')}"
            f"{webhook_data.get('StatusMessage', '')}"
            f"{self.private_key}"
        )
        
        calculated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()
        
        return calculated_hash == received_hash
    
    async def get_transaction_status(self, transaction_reference: str) -> Optional[Dict]:
        """
        Get the status of a transaction from Ozow API.
        """
        url = f"{self.api_url}/GetTransaction"
        
        headers = {
            "ApiKey": self.api_key,
            "SiteCode": self.site_code
        }
        
        params = {
            "transactionReference": transaction_reference
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error getting transaction status: {e}")
            return None
    
    async def initiate_refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None
    ) -> Dict:
        """
        Initiate a refund for a transaction.
        If amount is None, refunds the full amount.
        """
        url = f"{self.api_url}/RefundTransaction"
        
        headers = {
            "ApiKey": self.api_key,
            "SiteCode": self.site_code,
            "Content-Type": "application/json"
        }
        
        data = {
            "transactionId": transaction_id
        }
        
        if amount is not None:
            data["amount"] = int(amount * 100)  # Convert to cents
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error initiating refund: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
ozow_service = OzowPaymentService()
