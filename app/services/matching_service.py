from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.models.profile import Profile
from datetime import datetime, timedelta
import math
import uuid

class MatchingService:
    """Service for finding and ranking potential matches"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_matches(
        self,
        user_profile: Profile,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """
        Main matching function that returns ranked matches
        """
        # Step 1: Get all potential profiles
        all_profiles = await self._get_potential_profiles(user_profile)
        
        # Step 2: Apply hard filters
        filtered = await self._apply_filters(user_profile, all_profiles)
        
        # Step 3: Calculate compatibility scores
        scored_matches = []
        for profile in filtered:
            score = self._calculate_compatibility_score(user_profile, profile)
            scored_matches.append({
                "profile": profile,
                "score": score,
                "match_percentage": round(score, 2)
            })
        
        # Step 4: Apply boosts and rank
        boosted_matches = self._apply_boosts(user_profile, scored_matches)
        
        # Step 5: Sort by final score
        ranked = sorted(boosted_matches, key=lambda x: x["score"], reverse=True)
        
        # Step 6: Return paginated results
        return ranked[offset:offset + limit]
    
    async def _get_potential_profiles(self, user_profile: Profile) -> List[Profile]:
        """Get all discoverable profiles excluding self"""
        result = await self.db.execute(
            select(Profile).where(
                and_(
                    Profile.id != user_profile.id,
                    Profile.is_discoverable == True
                )
            )
        )
        return list(result.scalars().all())
    
    async def _apply_filters(
        self,
        user_profile: Profile,
        profiles: List[Profile]
    ) -> List[Profile]:
        """Apply hard filters (deal breakers, must-haves, etc.)"""
        filtered = []
        
        for profile in profiles:
            # Age range filter
            if user_profile.preferred_age_min and profile.age:
                if profile.age < user_profile.preferred_age_min:
                    continue
            if user_profile.preferred_age_max and profile.age:
                if profile.age > user_profile.preferred_age_max:
                    continue
            
            # Distance filter
            if user_profile.max_distance_km and user_profile.latitude and profile.latitude:
                distance = self._calculate_distance(
                    user_profile.latitude, user_profile.longitude,
                    profile.latitude, profile.longitude
                )
                if distance > user_profile.max_distance_km:
                    continue
            
            # Gender preference filter
            if user_profile.preferred_genders:
                if profile.gender and profile.gender.value not in user_profile.preferred_genders:
                    continue
            
            # Deal breakers
            if user_profile.deal_breakers:
                if self._has_deal_breaker(user_profile.deal_breakers, profile):
                    continue
            
            # Must haves
            if user_profile.must_haves:
                if not self._has_all_must_haves(user_profile.must_haves, profile, user_profile):
                    continue
            
            filtered.append(profile)
        
        return filtered
    
    def _calculate_compatibility_score(
        self,
        user_profile: Profile,
        match_profile: Profile
    ) -> float:
        """Calculate weighted compatibility score"""
        total_score = 0.0
        max_score = 0.0
        
        # Get user-defined weights or use defaults
        weights = user_profile.match_score_weight_preferences or {}
        weight_age = weights.get("age", 1.0)
        weight_distance = weights.get("distance", 1.0)
        weight_interests = weights.get("interests", 1.0)
        weight_values = weights.get("values", 1.0)
        weight_lifestyle = weights.get("lifestyle", 1.0)
        weight_personality = weights.get("personality", 1.0)
        weight_background = weights.get("background", 1.0)
        
        # Age compatibility (0-20 points)
        age_score = self._score_age_compatibility(user_profile, match_profile)
        total_score += age_score * 20 * weight_age
        max_score += 20
        
        # Distance score (0-15 points)
        distance_score = self._score_distance(user_profile, match_profile)
        total_score += distance_score * 15 * weight_distance
        max_score += 15
        
        # Interests overlap (0-25 points)
        interests_score = self._score_interests(
            user_profile.hobbies or [],
            match_profile.hobbies or []
        )
        total_score += interests_score * 25 * weight_interests
        max_score += 25
        
        # Values alignment (0-15 points)
        values_score = self._score_values(user_profile, match_profile)
        total_score += values_score * 15 * weight_values
        max_score += 15
        
        # Lifestyle compatibility (0-10 points)
        lifestyle_score = self._score_lifestyle(user_profile, match_profile)
        total_score += lifestyle_score * 10 * weight_lifestyle
        max_score += 10
        
        # Personality compatibility (0-10 points)
        personality_score = self._score_personality(user_profile, match_profile)
        total_score += personality_score * 10 * weight_personality
        max_score += 10
        
        # Background similarity (0-5 points)
        background_score = self._score_background(user_profile, match_profile)
        total_score += background_score * 5 * weight_background
        max_score += 5
        
        # Normalize to 0-100
        if max_score > 0:
            return (total_score / max_score) * 100
        return 0.0
    
    def _score_age_compatibility(
        self,
        user_profile: Profile,
        match_profile: Profile
    ) -> float:
        """Score based on age compatibility"""
        if not user_profile.age or not match_profile.age:
            return 0.5  # Neutral if age unknown
        
        age_diff = abs(user_profile.age - match_profile.age)
        
        # Perfect match if same age
        if age_diff == 0:
            return 1.0
        
        # Score decreases with age difference
        if age_diff <= 2:
            return 0.9
        elif age_diff <= 5:
            return 0.7
        elif age_diff <= 10:
            return 0.5
        else:
            return 0.3
    
    def _score_distance(
        self,
        user_profile: Profile,
        match_profile: Profile
    ) -> float:
        """Score based on distance (closer = higher score)"""
        if not all([user_profile.latitude, user_profile.longitude,
                   match_profile.latitude, match_profile.longitude]):
            return 0.5
        
        distance_km = self._calculate_distance(
            user_profile.latitude, user_profile.longitude,
            match_profile.latitude, match_profile.longitude
        )
        
        max_distance = user_profile.max_distance_km or 100
        
        # Score: 1.0 at 0km, 0.5 at 50% of max, 0.1 at max
        if distance_km == 0:
            return 1.0
        
        ratio = distance_km / max_distance
        if ratio >= 1.0:
            return 0.1
        elif ratio >= 0.5:
            return 0.5
        else:
            return 1.0 - (ratio * 0.5)
    
    def _score_interests(self, user_interests: List[str], match_interests: List[str]) -> float:
        """Jaccard similarity for interests"""
        if not user_interests or not match_interests:
            return 0.3  # Low score if no interests
        
        set_user = set(user_interests)
        set_match = set(match_interests)
        
        intersection = len(set_user & set_match)
        union = len(set_user | set_match)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _score_values(self, user_profile: Profile, match_profile: Profile) -> float:
        """Score based on values alignment"""
        score = 0.0
        factors = 0
        
        # Religion match
        if user_profile.religion and match_profile.religion:
            if user_profile.religion == match_profile.religion:
                score += 1.0
            factors += 1
        
        # Children preference match
        if user_profile.children_status and match_profile.children_status:
            if user_profile.children_status == match_profile.children_status:
                score += 1.0
            factors += 1
        
        # Values list overlap
        if user_profile.values and match_profile.values:
            values_score = self._score_interests(user_profile.values, match_profile.values)
            score += values_score
            factors += 1
        
        if factors == 0:
            return 0.5
        
        return score / factors
    
    def _score_lifestyle(
        self,
        user_profile: Profile,
        match_profile: Profile
    ) -> float:
        """Score based on lifestyle compatibility"""
        score = 0.0
        factors = 0
        
        # Drinking habits
        if user_profile.drinking_habit and match_profile.drinking_habit:
            if user_profile.drinking_habit == match_profile.drinking_habit:
                score += 1.0
            elif abs(self._drinking_level(user_profile.drinking_habit) - 
                    self._drinking_level(match_profile.drinking_habit)) <= 1:
                score += 0.7
            factors += 1
        
        # Smoking habits
        if user_profile.smoking_habit and match_profile.smoking_habit:
            if user_profile.smoking_habit == match_profile.smoking_habit:
                score += 1.0
            factors += 1
        
        # Lifestyle preference
        if user_profile.lifestyle_preference and match_profile.lifestyle_preference:
            if user_profile.lifestyle_preference == match_profile.lifestyle_preference:
                score += 1.0
            factors += 1
        
        if factors == 0:
            return 0.5
        
        return score / factors
    
    def _score_personality(
        self,
        user_profile: Profile,
        match_profile: Profile
    ) -> float:
        """Score based on personality compatibility"""
        # Similar personalities tend to work well together
        if user_profile.personality_type and match_profile.personality_type:
            if user_profile.personality_type == match_profile.personality_type:
                return 0.8  # Similar personalities
            else:
                return 0.6  # Different but potentially complementary
        
        return 0.5
    
    def _score_background(
        self,
        user_profile: Profile,
        match_profile: Profile
    ) -> float:
        """Score based on education/work background"""
        score = 0.0
        factors = 0
        
        # Education level
        if user_profile.education_level and match_profile.education_level:
            if user_profile.education_level == match_profile.education_level:
                score += 1.0
            factors += 1
        
        # Field of study (if same field)
        if user_profile.field_of_study and match_profile.field_of_study:
            if user_profile.field_of_study.lower() == match_profile.field_of_study.lower():
                score += 0.5
            factors += 1
        
        if factors == 0:
            return 0.5
        
        return score / factors
    
    def _apply_boosts(
        self,
        user_profile: Profile,
        matches: List[Dict]
    ) -> List[Dict]:
        """Apply boost factors to scores"""
        for match in matches:
            profile = match["profile"]
            base_score = match["score"]
            
            # Boost for recent activity
            if profile.last_active_at:
                hours_ago = (datetime.utcnow() - profile.last_active_at).total_seconds() / 3600
                if hours_ago < 1:
                    base_score += 5  # Active in last hour
                elif hours_ago < 24:
                    base_score += 3  # Active in last day
                elif hours_ago < 168:  # 1 week
                    base_score += 1
            
            # Boost for complete profile
            if profile.profile_completion_percentage:
                if profile.profile_completion_percentage >= 90:
                    base_score += 3
                elif profile.profile_completion_percentage >= 70:
                    base_score += 1
            
            # Boost for verified
            if profile.is_verified:
                base_score += 2
            
            match["score"] = min(100, base_score)  # Cap at 100
        
        return matches
    
    def _has_deal_breaker(self, deal_breakers: List[str], profile: Profile) -> bool:
        """Check if profile has any deal breaker"""
        if "smoking" in deal_breakers and profile.smoking_habit:
            if profile.smoking_habit.value in ["regularly", "occasionally"]:
                return True
        if "no_kids" in deal_breakers and profile.children_status:
            if profile.children_status.value == "has_children":
                return True
        if "drinking" in deal_breakers and profile.drinking_habit:
            if profile.drinking_habit.value in ["regularly", "heavily"]:
                return True
        return False
    
    def _has_all_must_haves(self, must_haves: List[str], profile: Profile, user_profile: Profile) -> bool:
        """Check if profile has all must-haves"""
        if "same_religion" in must_haves:
            if not profile.religion or profile.religion != user_profile.religion:
                return False
        if "same_education" in must_haves:
            if not profile.education_level or profile.education_level != user_profile.education_level:
                return False
        if "no_children" in must_haves:
            if profile.children_status and profile.children_status.value == "has_children":
                return False
        return True
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance in kilometers using Haversine formula"""
        R = 6371  # Earth radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _drinking_level(self, habit) -> int:
        """Convert drinking habit to numeric level"""
        if hasattr(habit, 'value'):
            habit = habit.value
        
        levels = {
            "never": 0,
            "occasionally": 1,
            "social_drinker": 2,
            "regularly": 3,
            "heavily": 4
        }
        return levels.get(habit, 2)

