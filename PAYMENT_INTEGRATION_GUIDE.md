# Payment Integration Guide

This guide explains how to integrate payments for the dating app using:
- **Ozow** for Next.js web app (South African payment gateway)
- **Google Play In-App Purchases** for Flutter Android app
- **Apple In-App Purchases** for Flutter iOS app

---

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Ozow Integration (Next.js)](#ozow-integration-nextjs)
3. [Google Play IAP (Flutter Android)](#google-play-iap-flutter-android)
4. [Apple IAP (Flutter iOS)](#apple-iap-flutter-ios)
5. [API Endpoints](#api-endpoints)
6. [Testing](#testing)

---

## Environment Setup

Add these variables to your `.env` file:

```env
# Ozow Payment Gateway (for Next.js web app)
OZOW_SITE_CODE=your-site-code
OZOW_PRIVATE_KEY=your-private-key
OZOW_API_KEY=your-api-key
OZOW_TEST_MODE=true  # Set to false for production

# Google Play In-App Purchases (for Flutter Android)
GOOGLE_PLAY_PACKAGE_NAME=com.yourapp.dating
GOOGLE_PLAY_SERVICE_ACCOUNT_FILE=/path/to/service-account.json

# Apple In-App Purchases (for Flutter iOS)
APPLE_SHARED_SECRET=your-shared-secret
APPLE_BUNDLE_ID=com.yourapp.dating
```

---

## Ozow Integration (Next.js)

### 1. Setup Ozow Account

1. Sign up at [Ozow](https://www.ozow.com/)
2. Get your Site Code, Private Key, and API Key
3. Configure webhook URL in Ozow dashboard: `https://your-api.com/payments/ozow/webhook`

### 2. Next.js Implementation

```typescript
// pages/api/purchase-credits.ts
import { useState } from 'react';

export default function PurchaseCredits() {
  const [loading, setLoading] = useState(false);

  const purchaseCredits = async (packageId: number) => {
    setLoading(true);
    
    try {
      // Get current URL for callbacks
      const baseUrl = window.location.origin;
      
      // Initiate payment
      const response = await fetch('/api/payments/ozow/initiate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${yourAuthToken}`
        },
        body: JSON.stringify({
          credit_package_id: packageId,
          success_url: `${baseUrl}/payment/success`,
          cancel_url: `${baseUrl}/payment/cancel`,
          error_url: `${baseUrl}/payment/error`,
          notify_url: `${baseUrl}/api/payments/ozow/webhook`
        })
      });
      
      const data = await response.json();
      
      // Create form and submit to Ozow
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = data.payment_url;
      
      // Add all payment data as hidden fields
      Object.keys(data.payment_data).forEach(key => {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = data.payment_data[key];
        form.appendChild(input);
      });
      
      document.body.appendChild(form);
      form.submit();
      
    } catch (error) {
      console.error('Payment error:', error);
      setLoading(false);
    }
  };

  return (
    <button onClick={() => purchaseCredits(1)} disabled={loading}>
      {loading ? 'Processing...' : 'Buy Credits'}
    </button>
  );
}
```

### 3. Payment Success Page

```typescript
// pages/payment/success.tsx
export default function PaymentSuccess() {
  return (
    <div>
      <h1>Payment Successful!</h1>
      <p>Your credits will be added to your account shortly.</p>
    </div>
  );
}
```

---

## Google Play IAP (Flutter Android)

### 1. Setup Google Play Console

1. Create app in Google Play Console
2. Set up in-app products:
   - **Credits**: One-time products (e.g., `credits_100`, `credits_500`)
   - **Premium**: Subscriptions (e.g., `premium_monthly`, `premium_yearly`)
3. Create service account and download JSON key
4. Enable Google Play Developer API

### 2. Flutter Implementation

Add dependency to `pubspec.yaml`:

```yaml
dependencies:
  in_app_purchase: ^3.1.0
```

```dart
// lib/services/payment_service.dart
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class PaymentService {
  final InAppPurchase _iap = InAppPurchase.instance;
  
  // Product IDs
  static const String credits100 = 'credits_100';
  static const String credits500 = 'credits_500';
  static const String premiumMonthly = 'premium_monthly';
  static const String premiumYearly = 'premium_yearly';
  
  Future<void> purchaseCredits(String productId, int creditsAmount) async {
    // Check if IAP is available
    final bool available = await _iap.isAvailable();
    if (!available) {
      throw Exception('In-app purchases not available');
    }
    
    // Get product details
    final ProductDetailsResponse response = await _iap.queryProductDetails({productId});
    
    if (response.productDetails.isEmpty) {
      throw Exception('Product not found');
    }
    
    final ProductDetails productDetails = response.productDetails.first;
    
    // Create purchase param
    final PurchaseParam purchaseParam = PurchaseParam(
      productDetails: productDetails,
    );
    
    // Start purchase
    await _iap.buyConsumable(purchaseParam: purchaseParam);
  }
  
  Future<void> verifyPurchase(PurchaseDetails purchase, int creditsAmount) async {
    // Verify with backend
    final response = await http.post(
      Uri.parse('https://your-api.com/payments/iap/verify-google-play'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $yourAuthToken',
      },
      body: jsonEncode({
        'payment_type': 'credits',
        'product_id': purchase.productID,
        'purchase_token': purchase.verificationData.serverVerificationData,
        'credits_amount': creditsAmount,
      }),
    );
    
    if (response.statusCode == 200) {
      // Mark purchase as complete
      await _iap.completePurchase(purchase);
    } else {
      throw Exception('Purchase verification failed');
    }
  }
  
  void listenToPurchases() {
    _iap.purchaseStream.listen((purchases) {
      for (var purchase in purchases) {
        if (purchase.status == PurchaseStatus.purchased) {
          // Verify and complete purchase
          verifyPurchase(purchase, getCreditsAmount(purchase.productID));
        }
      }
    });
  }
  
  int getCreditsAmount(String productId) {
    switch (productId) {
      case credits100:
        return 100;
      case credits500:
        return 500;
      default:
        return 0;
    }
  }
}
```

---

## Apple IAP (Flutter iOS)

### 1. Setup App Store Connect

1. Create app in App Store Connect
2. Set up in-app purchases:
   - **Credits**: Consumable (e.g., `credits_100`, `credits_500`)
   - **Premium**: Auto-renewable subscriptions (e.g., `premium_monthly`, `premium_yearly`)
3. Get shared secret from App Store Connect

### 2. Flutter Implementation

Same as Google Play, but verification endpoint is different:

```dart
Future<void> verifyApplePurchase(PurchaseDetails purchase, int creditsAmount) async {
  final response = await http.post(
    Uri.parse('https://your-api.com/payments/iap/verify-apple'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $yourAuthToken',
    },
    body: jsonEncode({
      'payment_type': 'credits',
      'receipt_data': purchase.verificationData.serverVerificationData,
      'credits_amount': creditsAmount,
    }),
  );
  
  if (response.statusCode == 200) {
    await _iap.completePurchase(purchase);
  } else {
    throw Exception('Purchase verification failed');
  }
}
```

---

## API Endpoints

### Get Credit Packages

```http
GET /payments/credit-packages
Authorization: Bearer {token}
```

Response:
```json
[
  {
    "id": 1,
    "name": "Starter Pack",
    "credits": 100,
    "price": 49.99,
    "bonus_credits": 10,
    "is_popular": false,
    "total_credits": 110
  }
]
```

### Get Premium Plans

```http
GET /payments/premium-plans
Authorization: Bearer {token}
```

Response:
```json
[
  {
    "id": 1,
    "name": "Monthly Premium",
    "plan_type": "premium_monthly",
    "duration_days": 30,
    "price": 99.99,
    "is_popular": true,
    "features": [
      "Unlimited likes",
      "See who liked you",
      "Advanced filters"
    ]
  }
]
```

### Initiate Ozow Payment (Web)

```http
POST /payments/ozow/initiate
Authorization: Bearer {token}
Content-Type: application/json

{
  "credit_package_id": 1,
  "success_url": "https://yourapp.com/payment/success",
  "cancel_url": "https://yourapp.com/payment/cancel",
  "error_url": "https://yourapp.com/payment/error",
  "notify_url": "https://yourapi.com/payments/ozow/webhook"
}
```

### Verify Google Play Purchase (Mobile)

```http
POST /payments/iap/verify-google-play
Authorization: Bearer {token}
Content-Type: application/json

{
  "payment_type": "credits",
  "product_id": "credits_100",
  "purchase_token": "...",
  "credits_amount": 100
}
```

### Verify Apple Purchase (Mobile)

```http
POST /payments/iap/verify-apple
Authorization: Bearer {token}
Content-Type: application/json

{
  "payment_type": "credits",
  "receipt_data": "...",
  "credits_amount": 100
}
```

### Get Subscription Status

```http
GET /payments/subscription
Authorization: Bearer {token}
```

---

## Testing

### Ozow Testing

1. Set `OZOW_TEST_MODE=true` in `.env`
2. Use Ozow test cards:
   - **Success**: Use any valid card number
   - **Failure**: Use card number `4000000000000002`

### Google Play Testing

1. Add test accounts in Google Play Console
2. Use test product IDs
3. Purchases will be free for test accounts

### Apple Testing

1. Create sandbox tester account in App Store Connect
2. Sign in with sandbox account on iOS device
3. Purchases will be free for sandbox accounts

---

## Database Setup

Before using payments, seed the database with packages and plans:

```sql
-- Credit packages
INSERT INTO credit_packages (name, credits, price, bonus_credits, is_popular, display_order, is_active)
VALUES
  ('Starter Pack', 100, 49.99, 10, false, 1, true),
  ('Popular Pack', 500, 199.99, 100, true, 2, true),
  ('Best Value', 1000, 349.99, 300, false, 3, true);

-- Premium plans
INSERT INTO premium_plans (name, plan_type, duration_days, price, original_price, is_popular, display_order, is_active, features)
VALUES
  ('Monthly Premium', 'premium_monthly', 30, 99.99, NULL, false, 1, true, 
   '["Unlimited likes", "See who liked you", "Advanced filters", "Read receipts", "Profile boost", "Rewind"]'::json),
  ('Yearly Premium', 'premium_yearly', 365, 999.99, 1199.88, true, 2, true,
   '["Unlimited likes", "See who liked you", "Advanced filters", "Read receipts", "Profile boost", "Rewind", "Save 17%"]'::json);
```

---

## Security Notes

1. **Never expose private keys** in frontend code
2. **Always verify purchases** on the backend
3. **Use HTTPS** for all payment endpoints
4. **Validate webhook signatures** (Ozow hash verification)
5. **Store sensitive data** (service account files) securely
6. **Test thoroughly** before going to production

---

## Support

- **Ozow**: https://www.ozow.com/support
- **Google Play**: https://support.google.com/googleplay/android-developer
- **Apple**: https://developer.apple.com/support/app-store/

