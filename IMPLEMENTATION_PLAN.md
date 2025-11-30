# Implementation Plan - South African Dating App

## Phase 1: Core Foundation ✅ (COMPLETED)

### 1.1 Database Models ✅
- [x] Profile model with matching fields
- [x] UserMedia model
- [x] Conversation and Message models
- [x] Like/Super Like model
- [x] Credit system models
- [x] Verification model
- [x] Profile views model
- [x] All enums (Gender, Sexuality, etc.)

### 1.2 Authentication ✅
- [x] Supabase Auth integration
- [x] JWT verification via JWKS
- [x] OAuth support (Google, GitHub)
- [x] Profile creation on signup

### 1.3 Basic Services ✅
- [x] Matching service (filtering & scoring)
- [x] Credit service
- [x] AI icebreaker service
- [x] Content moderation service
- [x] Supabase Storage service
- [x] Supabase Realtime service

---

## Phase 2: Database Migration & Setup 🔄 (IN PROGRESS)

### 2.1 Create Database Migration
**Priority: HIGH | Estimated Time: 30 min**

Steps:
1. Review all new models
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Add matching fields, likes, credits, verification"
   ```
3. Review generated migration file
4. Test migration on development database
5. Apply migration:
   ```bash
   alembic upgrade head
   ```

**Files to check:**
- `migrations/versions/` - New migration file
- Verify all tables are created correctly

### 2.2 Update Supabase Database
**Priority: HIGH | Estimated Time: 15 min**

Steps:
1. Connect to Supabase dashboard
2. Verify tables created via migration
3. Set up Row Level Security (RLS) policies:
   - Profiles: Users can read all, update own
   - Likes: Users can create own, read received
   - Messages: Users can read conversations they're in
   - Credits: Users can only see own transactions
4. Create indexes for performance:
   - `likes(liker_id, liked_id)`
   - `profile_views(viewer_id, viewed_id)`
   - `profiles(latitude, longitude)` for location queries

---

## Phase 3: Core API Endpoints 🔄 (IN PROGRESS)

### 3.1 Verification API Routes
**Priority: HIGH | Estimated Time: 2 hours**

**File:** `app/api/routes/verification.py`

Endpoints needed:
- `POST /verification/photo` - Upload photo for verification
- `POST /verification/video` - Upload video for verification
- `GET /verification/status` - Check verification status
- `POST /verification/photo/verify` - Submit selfie with code
- `PUT /verification/{id}/approve` - Admin approve (if needed)

**Implementation steps:**
1. Create verification route file
2. Add photo upload endpoint (store in Supabase Storage)
3. Add video upload endpoint (validate 30-60 seconds)
4. Generate verification code for photo verification
5. Add status check endpoint
6. Update profile verification flags on approval
7. Add to main.py router

**Dependencies:**
- Supabase Storage service
- Content moderation for uploaded media

### 3.2 Discovery & Browse API
**Priority: HIGH | Estimated Time: 3 hours**

**File:** `app/api/routes/discovery.py`

Endpoints needed:
- `GET /discovery/daily-matches` - Get curated daily matches
- `GET /discovery/browse` - Browse with filters
- `GET /discovery/nearby` - Location-based discovery
- `GET /discovery/recently-active` - Recently active profiles
- `GET /discovery/new-profiles` - New signups

**Implementation steps:**
1. Create discovery route file
2. Implement daily matches (use matching service, limit to 10-20)
3. Implement browse with filters:
   - Age range
   - Distance
   - Gender
   - Relationship type
   - Interests
   - Education level
   - etc.
4. Implement location-based discovery (South Africa specific)
5. Add recently active (last 24 hours)
6. Add new profiles (last 7 days)
7. Add pagination
8. Add to main.py router

**Dependencies:**
- Matching service
- Profile model with location data

### 3.3 Enhanced Messages API
**Priority: HIGH | Estimated Time: 2 hours**

**File:** `app/api/routes/messages.py` (update existing)

New features needed:
- Credit check for messaging unmatched users
- One message limit until reply
- AI icebreaker suggestions endpoint

**Implementation steps:**
1. Update `POST /messages` to check if users are matched
2. If not matched:
   - Check if user has credits
   - Deduct credits
   - Allow only one message
   - Create conversation but mark as "pending reply"
3. Add `GET /messages/icebreakers/{profile_id}` - Get AI icebreakers
4. Add logic to allow continued conversation after reply
5. Update message sending logic

**Dependencies:**
- Credit service
- AI icebreaker service
- Like model (to check matches)

### 3.4 Credits & Payments API
**Priority: MEDIUM | Estimated Time: 4 hours**

**File:** `app/api/routes/credits.py`

Endpoints needed:
- `GET /credits/balance` - Get current balance
- `GET /credits/transactions` - Get transaction history
- `POST /credits/purchase` - Purchase credits (payment integration)
- `GET /credits/pricing` - Get credit pricing

**Implementation steps:**
1. Create credits route file
2. Add balance endpoint
3. Add transaction history endpoint
4. Add credit purchase endpoint (integrate payment gateway)
5. Add pricing endpoint
6. Add to main.py router

**Payment Gateway Integration:**
- Research South African payment gateways (PayFast, Paystack, etc.)
- Implement webhook handler for payment confirmation
- Update credit balance on successful payment

**Dependencies:**
- Credit service
- Payment gateway SDK

### 3.5 Analytics API
**Priority: MEDIUM | Estimated Time: 2 hours**

**File:** `app/api/routes/analytics.py`

Endpoints needed:
- `GET /analytics/profile-stats` - Profile views, likes, matches
- `GET /analytics/like-stats` - Like statistics
- `GET /analytics/match-stats` - Match success rate
- `GET /analytics/response-stats` - Response time analytics

**Implementation steps:**
1. Create analytics route file
2. Implement profile stats (views, likes received, matches)
3. Implement like stats (sent, received, match rate)
4. Implement match stats (total matches, conversion rate)
5. Implement response time stats (average response time)
6. Add to main.py router

**Dependencies:**
- Profile views model
- Like model
- Message model

---

## Phase 4: Premium Features 🔄 (PENDING)

### 4.1 Premium Subscription System
**Priority: MEDIUM | Estimated Time: 3 hours**

**File:** `app/api/routes/premium.py`

Endpoints needed:
- `GET /premium/status` - Check premium status
- `POST /premium/subscribe` - Subscribe to premium
- `POST /premium/cancel` - Cancel subscription
- `GET /premium/features` - List premium features

**Features:**
- Unlimited likes
- See who liked you
- Advanced filters
- Read receipts
- Profile boost
- Rewind (undo swipe)

**Implementation steps:**
1. Create premium route file
2. Add subscription endpoint (integrate payment)
3. Add cancel endpoint
4. Add status check endpoint
5. Update matching service to check premium status
6. Update likes API to allow unlimited for premium
7. Add premium badge to profile response
8. Add to main.py router

**Dependencies:**
- Payment gateway
- Profile model (is_premium field)

### 4.2 Premium Feature Implementation
**Priority: MEDIUM | Estimated Time: 4 hours**

**Features to implement:**
1. **Unlimited Likes:**
   - Update likes API to skip credit check for premium users
   - Remove daily like limit for premium

2. **See Who Liked You:**
   - Update `/likes/received` to show full profiles for premium
   - Free users see blurred/limited info

3. **Advanced Filters:**
   - Add more filter options in discovery API
   - Education, income, height, etc.

4. **Read Receipts:**
   - Track message read status
   - Show read receipts in message response (premium only)

5. **Profile Boost:**
   - Boost profile visibility in discovery
   - Higher in match rankings
   - Show "Boosted" badge

6. **Rewind:**
   - Store last 10 swipes/likes
   - Allow undo for premium users

**Dependencies:**
- Premium subscription system
- Enhanced discovery API

---

## Phase 5: Safety & Moderation 🔄 (PENDING)

### 5.1 Content Moderation Integration
**Priority: HIGH | Estimated Time: 3 hours**

**Implementation steps:**
1. Integrate content moderation in media upload:
   - Moderate videos before approval
   - Moderate photos
   - Moderate bio text
2. Add moderation status to UserMedia model
3. Auto-reject inappropriate content
4. Flag for manual review if uncertain
5. Send notifications for rejected content

**Dependencies:**
- Content moderation service (already created)
- Media upload endpoints

### 5.2 Report & Block System
**Priority: HIGH | Estimated Time: 2 hours**

**File:** `app/models/report.py`, `app/api/routes/reports.py`

**Implementation steps:**
1. Create Report model:
   - Reporter ID
   - Reported profile ID
   - Report type (inappropriate, spam, fake, etc.)
   - Reason
   - Status (pending, reviewed, resolved)
2. Create Block model:
   - Blocker ID
   - Blocked profile ID
3. Create report endpoints:
   - `POST /reports` - Report a profile
   - `GET /reports` - Get user's reports (admin)
4. Create block endpoints:
   - `POST /block/{profile_id}` - Block a user
   - `DELETE /block/{profile_id}` - Unblock
   - `GET /blocked` - Get blocked users
5. Update matching service to exclude blocked users
6. Update messages API to prevent messaging blocked users

**Dependencies:**
- Profile model
- Matching service

### 5.3 Safe Meeting Tips
**Priority: LOW | Estimated Time: 1 hour**

**File:** `app/api/routes/safety.py`

**Implementation steps:**
1. Create safety tips endpoint
2. Return safety guidelines
3. Add to profile or match response

---

## Phase 6: Enhanced Features 🔄 (PENDING)

### 6.1 Profile Completion Flow
**Priority: MEDIUM | Estimated Time: 2 hours**

**Implementation steps:**
1. Create onboarding checklist
2. Track required vs optional fields
3. Show completion percentage
4. Add reminders for incomplete profiles
5. Require intro video before profile is active
6. Add progress indicator in API response

**Dependencies:**
- Profile model (already has completion percentage)

### 6.2 Location Services
**Priority: MEDIUM | Estimated Time: 2 hours**

**South Africa Specific:**
1. Validate locations are in South Africa
2. Add South African cities/provinces
3. Calculate distance between users
4. Location-based matching
5. Show province/city in profiles

**Implementation steps:**
1. Add South African location data (cities, provinces)
2. Validate location on profile update
3. Update matching service for location
4. Add location filters in discovery

### 6.3 Notification System
**Priority: MEDIUM | Estimated Time: 3 hours**

**Notifications needed:**
- New match
- New like
- New message
- Profile view
- Verification approved/rejected
- Credit purchase confirmation

**Implementation steps:**
1. Create Notification model
2. Create notification service
3. Integrate with Supabase Realtime or push notifications
4. Create notification endpoints
5. Mark as read functionality

**Dependencies:**
- Supabase Realtime (already set up)

---

## Phase 7: Testing & Optimization 🔄 (PENDING)

### 7.1 Unit Tests
**Priority: MEDIUM | Estimated Time: 4 hours**

**Test files needed:**
- `tests/test_matching_service.py`
- `tests/test_credit_service.py`
- `tests/test_ai_icebreaker.py`
- `tests/test_content_moderation.py`
- `tests/test_auth.py`
- `tests/test_likes.py`

### 7.2 Integration Tests
**Priority: MEDIUM | Estimated Time: 3 hours**

**Test scenarios:**
- Complete user flow (signup → profile → match → message)
- Credit purchase and usage
- Premium subscription flow
- Verification flow
- Report and block flow

### 7.3 Performance Optimization
**Priority: MEDIUM | Estimated Time: 3 hours**

**Optimizations:**
1. Add database indexes
2. Cache frequently accessed data
3. Optimize matching algorithm
4. Pagination for large result sets
5. Image/video optimization
6. Query optimization

---

## Phase 8: Documentation & Deployment 🔄 (PENDING)

### 8.1 API Documentation
**Priority: LOW | Estimated Time: 2 hours**

**Steps:**
1. Update FastAPI docstrings
2. Add examples to endpoints
3. Document error responses
4. Create API usage guide

### 8.2 Deployment Setup
**Priority: HIGH | Estimated Time: 4 hours**

**Steps:**
1. Set up production environment variables
2. Configure Supabase for production
3. Set up CI/CD pipeline
4. Database backup strategy
5. Monitoring and logging
6. Error tracking (Sentry, etc.)

---

## Priority Order Summary

### 🔴 CRITICAL (Do First)
1. ✅ Database migration
2. ✅ Verification API routes
3. ✅ Discovery & Browse API
4. ✅ Enhanced Messages API (credit check)
5. ✅ Report & Block system

### 🟡 HIGH PRIORITY (Do Next)
6. Credits & Payments API
7. Content moderation integration
8. Premium subscription system
9. Analytics API
10. Profile completion flow

### 🟢 MEDIUM PRIORITY (Do After)
11. Premium features implementation
12. Location services (South Africa)
13. Notification system
14. Testing
15. Performance optimization

### ⚪ LOW PRIORITY (Nice to Have)
16. Safe meeting tips
17. API documentation
18. Advanced analytics

---

## Estimated Timeline

- **Phase 2 (Migration)**: 1 day
- **Phase 3 (Core APIs)**: 1-2 weeks
- **Phase 4 (Premium)**: 1 week
- **Phase 5 (Safety)**: 1 week
- **Phase 6 (Enhanced)**: 1 week
- **Phase 7 (Testing)**: 1 week
- **Phase 8 (Deployment)**: 3-5 days

**Total: ~6-8 weeks for full implementation**

---

## Quick Start Checklist

Before starting development, ensure:
- [ ] Database migration created and tested
- [ ] Supabase project configured
- [ ] Environment variables set up
- [ ] AI API keys obtained (OpenAI/Gemini/DeepSeek)
- [ ] Payment gateway account created (PayFast/Paystack)
- [ ] South African location data prepared
- [ ] Content moderation API keys ready

---

## Notes

- **South Africa Focus**: All location features should be South Africa-specific
- **Video Requirement**: Intro video (30-60 sec) is mandatory for profile activation
- **Credit System**: Core monetization - implement early
- **Safety First**: Report/block system is critical for user safety
- **AI Integration**: Icebreakers and moderation use AI - have fallbacks ready

