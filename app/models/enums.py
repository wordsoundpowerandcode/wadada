from enum import Enum

class RelationshipType(str, Enum):
    """Type of relationship user is looking for"""
    CASUAL_DATING = "casual_dating"
    SERIOUS_RELATIONSHIP = "serious_relationship"
    MARRIAGE = "marriage"
    FRIENDSHIP = "friendship"
    SOMETHING_CASUAL = "something_casual"
    NOT_SURE = "not_sure"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    TRANSGENDER = "transgender"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    OTHER = "other"

class Sexuality(str, Enum):
    STRAIGHT = "straight"
    GAY = "gay"
    LESBIAN = "lesbian"
    BISEXUAL = "bisexual"
    PANSEXUAL = "pansexual"
    ASEXUAL = "asexual"
    DEMISEXUAL = "demisexual"
    QUEER = "queer"
    QUESTIONING = "questioning"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class RelationshipStatus(str, Enum):
    SINGLE = "single"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    NEVER_MARRIED = "never_married"

class DrinkingHabit(str, Enum):
    NEVER = "never"
    OCCASIONALLY = "occasionally"
    SOCIAL_DRINKER = "social_drinker"
    REGULARLY = "regularly"
    HEAVILY = "heavily"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class SmokingHabit(str, Enum):
    NEVER = "never"
    OCCASIONALLY = "occasionally"
    REGULARLY = "regularly"
    QUIT = "quit"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class BodyType(str, Enum):
    SLIM = "slim"
    ATHLETIC = "athletic"
    AVERAGE = "average"
    CURVY = "curvy"
    MUSCULAR = "muscular"
    LARGE = "large"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class EducationLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    DOCTORATE = "doctorate"
    PROFESSIONAL = "professional"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class Religion(str, Enum):
    CHRISTIANITY = "christianity"
    ISLAM = "islam"
    HINDUISM = "hinduism"
    BUDDHISM = "buddhism"
    JUDAISM = "judaism"
    SIKHISM = "sikhism"
    ATHEIST = "atheist"
    AGNOSTIC = "agnostic"
    SPIRITUAL = "spiritual"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class ChildrenStatus(str, Enum):
    NO_CHILDREN = "no_children"
    HAS_CHILDREN = "has_children"
    WANTS_CHILDREN = "wants_children"
    DOESNT_WANT_CHILDREN = "doesnt_want_children"
    NOT_SURE = "not_sure"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class PetPreference(str, Enum):
    LOVES_PETS = "loves_pets"
    HAS_PETS = "has_pets"
    ALLERGIC = "allergic"
    DOESNT_LIKE = "doesnt_like"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class PersonalityType(str, Enum):
    INTROVERT = "introvert"
    EXTROVERT = "extrovert"
    AMBIVERT = "ambivert"

class LifestylePreference(str, Enum):
    NIGHT_OWL = "night_owl"
    EARLY_BIRD = "early_bird"
    HOME_BODY = "home_body"
    ADVENTUROUS = "adventurous"
    SOCIAL_BUTTERFLY = "social_butterfly"
    BALANCED = "balanced"

class CommunicationStyle(str, Enum):
    DIRECT = "direct"
    GENTLE = "gentle"
    HUMOROUS = "humorous"
    THOUGHTFUL = "thoughtful"
    PLAYFUL = "playful"

