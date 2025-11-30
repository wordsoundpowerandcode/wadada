# Implementation Checklist - New Features

## ✅ Completed Tasks

### 1. Verification API
- [x] Created `app/api/routes/verification.py`
- [x] Created `app/schemas/verification.py`
- [x] Implemented photo verification with code
- [x] Implemented video verification
- [x] Added content moderation integration
- [x] Added status checking endpoint
- [x] Added admin approve/reject endpoints
- [x] Integrated with Supabase Storage

### 2. Discovery API
- [x] Created `app/api/routes/discovery.py`
- [x] Created `app/schemas/discovery.py`
- [x] Implemented daily matches
- [x] Implemented browse with filters
- [x] Implemented nearby profiles (location-based)
- [x] Implemented recently active profiles
- [x] Implemented new profiles
- [x] Implemented random discovery
- [x] Added premium filter support
- [x] Added pagination

### 3. Payment Integration
- [x] Created `app/models/payment.py`
- [x] Created `app/services/ozow_payment.py`
- [x] Created `app/services/iap_service.py`
- [x] Created `app/api/routes/payments.py`
- [x] Created `app/schemas/payment.py`
- [x] Implemented Ozow payment (South African web)
- [x] Implemented Google Play IAP (Android)
- [x] Implemented Apple IAP (iOS)
- [x] Added webhook handling for Ozow
- [x] Added purchase verification
- [x] Added subscription management
- [x] Created payment integration guide

### 4. Configuration & Setup
- [x] Updated `app/config.py` with payment settings
- [x] Updated `app/main.py` with new routers
- [x] Added `google-auth` to requirements.txt
- [x] Created `PAYMENT_INTEGRATION_GUIDE.md`
- [x] Created `NEW_FEATURES_SUMMARY.md`

---

## 🔄 Next Steps (To Do)

### 1. Database Migration (HIGH PRIORITY)
- [ ] Run database migration to create new tables:
  ```bash
  alembic revision --autogenerate -m "Add verification, payment models"
  alembic upgrade head
  ```

### 2. Seed Database (HIGH PRIORITY)
- [ ] Add credit packages to database
- [ ] Add premium plans to database
- [ ] Use SQL script from `NEW_FEATURES_SUMMARY.md`

### 3. Payment Provider Setup (HIGH PRIORITY)

#### Ozow (for Next.js)
- [ ] Sign up for Ozow account at https://www.ozow.com/
- [ ] Get Site Code, Private Key, and API Key
- [ ] Configure webhook URL in Ozow dashboard
- [ ] Add credentials to `.env` file
- [ ] Test in test mode

#### Google Play (for Flutter Android)
- [ ] Create app in Google Play Console
- [ ] Set up in-app products (credits and subscriptions)
- [ ] Create service account
- [ ] Download service account JSON key
- [ ] Enable Google Play Developer API
- [ ] Add credentials to `.env` file

#### Apple (for Flutter iOS)
- [ ] Create app in App Store Connect
- [ ] Set up in-app purchases (consumables and subscriptions)
- [ ] Get shared secret from App Store Connect
- [ ] Add credentials to `.env` file

### 4. Environment Variables (HIGH PRIORITY)
Add to `.env` file:

```env
# Ozow Payment Gateway
OZOW_SITE_CODE=your-site-code
OZOW_PRIVATE_KEY=your-private-key
OZOW_API_KEY=your-api-key
OZOW_TEST_MODE=true

# Google Play IAP
GOOGLE_PLAY_PACKAGE_NAME=com.yourapp.dating
GOOGLE_PLAY_SERVICE_ACCOUNT_FILE=/path/to/service-account.json

# Apple IAP
APPLE_SHARED_SECRET=your-shared-secret
APPLE_BUNDLE_ID=com.yourapp.dating
```

### 5. Install Dependencies (MEDIUM PRIORITY)
```bash
pip install -r requirements.txt
```

### 6. Testing (MEDIUM PRIORITY)

#### Verification API
- [ ] Test photo verification code generation
- [ ] Test photo upload with valid code
- [ ] Test photo upload with invalid code
- [ ] Test video upload
- [ ] Test content moderation rejection
- [ ] Test verification status endpoint
- [ ] Test admin approve/reject

#### Discovery API
- [ ] Test daily matches with sample data
- [ ] Test browse with basic filters
- [ ] Test browse with premium filters
- [ ] Test nearby profiles (requires location data)
- [ ] Test recently active profiles
- [ ] Test new profiles
- [ ] Test pagination

#### Payment Integration
- [ ] Test Ozow payment initiation
- [ ] Test Ozow webhook (use Ozow test mode)
- [ ] Test Google Play purchase verification
- [ ] Test Apple purchase verification
- [ ] Test credit addition after purchase
- [ ] Test premium activation after subscription
- [ ] Test subscription status endpoint

### 7. Frontend Integration (MEDIUM PRIORITY)

#### Next.js Web App
- [ ] Implement credit purchase flow with Ozow
- [ ] Implement premium subscription flow with Ozow
- [ ] Create payment success/cancel/error pages
- [ ] Add verification UI (photo/video upload)
- [ ] Add discovery UI (daily matches, browse)
- [ ] Test end-to-end payment flow

#### Flutter Mobile App
- [ ] Add `in_app_purchase` package
- [ ] Implement credit purchase with IAP
- [ ] Implement premium subscription with IAP
- [ ] Add purchase verification flow
- [ ] Add verification UI (photo/video upload)
- [ ] Add discovery UI (daily matches, browse)
- [ ] Test on both Android and iOS

### 8. Security & Production (LOW PRIORITY)
- [ ] Set up HTTPS for all endpoints
- [ ] Add rate limiting to payment endpoints
- [ ] Set up error tracking (Sentry)
- [ ] Set up payment logging
- [ ] Review and test webhook security
- [ ] Test refund flow
- [ ] Set production credentials
- [ ] Disable test mode

### 9. Documentation (LOW PRIORITY)
- [ ] Update API documentation
- [ ] Create user guide for verification
- [ ] Create user guide for payments
- [ ] Document error codes
- [ ] Create troubleshooting guide

---

## 📊 Progress Tracking

### Overall Progress: 60%

- ✅ Backend Implementation: 100%
- 🔄 Database Setup: 0%
- 🔄 Payment Provider Setup: 0%
- 🔄 Testing: 0%
- 🔄 Frontend Integration: 0%
- 🔄 Production Deployment: 0%

---

## 🚨 Critical Path

To get the features working, follow this order:

1. **Database Migration** (30 min)
2. **Seed Database** (15 min)
3. **Install Dependencies** (5 min)
4. **Add Environment Variables** (10 min)
5. **Test Verification API** (1 hour)
6. **Test Discovery API** (1 hour)
7. **Setup Ozow Test Account** (30 min)
8. **Test Ozow Payment** (1 hour)
9. **Frontend Integration** (4-6 hours)
10. **End-to-End Testing** (2-3 hours)

**Total Estimated Time**: 12-15 hours

---

## 📝 Notes

### Important Reminders
- Always verify purchases on the backend (never trust client)
- Use test mode for all payment providers initially
- Keep private keys secure (never commit to git)
- Test webhook endpoints thoroughly
- Monitor payment transactions closely

### Known Limitations
- Distance calculation uses approximate Haversine formula (consider PostGIS for production)
- Video duration validation not implemented (requires ffmpeg)
- Random profile discovery uses `ORDER BY RANDOM()` (not ideal for large datasets)
- Manual review required for some verifications

### Future Enhancements
- Add video duration validation
- Implement PostGIS for accurate distance calculation
- Add payment analytics dashboard
- Add fraud detection
- Add payment retry logic
- Add subscription renewal reminders
- Add promotional codes/discounts

---

## 📞 Support Resources

- **Ozow Documentation**: https://docs.ozow.com/
- **Google Play Billing**: https://developer.android.com/google/play/billing
- **Apple StoreKit**: https://developer.apple.com/storekit/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Supabase Documentation**: https://supabase.com/docs

---

## ✅ Ready for Next Phase

All backend code is complete and ready for:
1. Database migration
2. Testing
3. Frontend integration
4. Production deployment

See `PAYMENT_INTEGRATION_GUIDE.md` for detailed integration instructions.
See `NEW_FEATURES_SUMMARY.md` for feature overview and API documentation.

