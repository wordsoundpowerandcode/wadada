# Migration Notes for Extended Profile Model

## Overview
The Profile model has been extended with comprehensive matching fields. You need to create and run a migration to add these fields to your database.

## Steps to Create Migration

1. **Generate the migration:**
   ```bash
   alembic revision --autogenerate -m "Add matching fields to profiles"
   ```

2. **Review the generated migration file** in `migrations/versions/` to ensure all fields are included.

3. **Apply the migration:**
   ```bash
   alembic upgrade head
   ```

## New Fields Added

### Demographics
- `date_of_birth` (date)
- `age` (integer)
- `gender` (enum: Gender)
- `sexuality` (enum: Sexuality)
- `height_cm` (integer)
- `body_type` (enum: BodyType)
- `current_city` (string)
- `current_country` (string)
- `latitude` (float)
- `longitude` (float)
- `timezone` (string)

### Relationship & Dating
- `relationship_status` (enum: RelationshipStatus)
- `relationship_type_seeking` (enum: RelationshipType)
- `dating_goals_timeline` (string)

### Work & Education
- `occupation` (string)
- `company` (string)
- `education_level` (enum: EducationLevel)
- `school` (string)
- `field_of_study` (string)

### Lifestyle & Habits
- `drinking_habit` (enum: DrinkingHabit)
- `smoking_habit` (enum: SmokingHabit)
- `exercise_frequency` (string)
- `diet_preference` (string)

### Family & Pets
- `children_status` (enum: ChildrenStatus)
- `wants_more_children` (boolean)
- `pet_preference` (enum: PetPreference)
- `has_pets` (boolean)
- `pet_types` (array of strings)

### Personal Values
- `religion` (enum: Religion)
- `religion_importance` (string)
- `political_views` (string)
- `values` (array of strings)

### Personality & Interests
- `personality_type` (enum: PersonalityType)
- `lifestyle_preference` (enum: LifestylePreference)
- `communication_style` (enum: CommunicationStyle)
- `hobbies` (array of strings)
- `interests` (array of strings)
- `favorite_activities` (array of strings)
- `languages_spoken` (array of strings)

### Match Preferences
- `preferred_age_min` (integer)
- `preferred_age_max` (integer)
- `preferred_genders` (array of strings)
- `preferred_relationship_types` (array of strings)
- `max_distance_km` (integer)
- `deal_breakers` (array of strings)
- `must_haves` (array of strings)

### Additional Matching Fields
- `energy_level` (string)
- `social_activity_level` (string)
- `travel_frequency` (string)
- `work_life_balance` (string)
- `financial_situation` (string)

### Compatibility & Matching
- `profile_completion_percentage` (integer, default: 0)
- `last_active_at` (datetime)
- `is_verified` (boolean, default: False)
- `is_premium` (boolean, default: False)
- `match_score_weight_preferences` (JSON)

### Privacy & Discovery
- `is_discoverable` (boolean, default: True)
- `show_age` (boolean, default: True)
- `show_distance` (boolean, default: True)
- `show_last_active` (boolean, default: True)

## New Enums Created

All enums are defined in `app/models/enums.py`:
- RelationshipType
- Gender
- Sexuality
- RelationshipStatus
- DrinkingHabit
- SmokingHabit
- BodyType
- EducationLevel
- Religion
- ChildrenStatus
- PetPreference
- PersonalityType
- LifestylePreference
- CommunicationStyle

## New API Endpoints

### Matches
- `GET /matches` - Get potential matches (paginated)
- `GET /matches/count` - Get total count of potential matches

## Matching Service

A new `MatchingService` has been created in `app/services/matching_service.py` that:
1. Filters profiles based on hard requirements (age, distance, deal breakers, etc.)
2. Calculates compatibility scores based on multiple factors
3. Applies boost factors (recent activity, profile completeness, verification)
4. Ranks matches by final score

## Profile Completion

The profile update endpoint now automatically calculates `profile_completion_percentage` based on filled fields.

