from djongo import models
from django_enumfield import enum
from uuid import uuid4
from typing import Optional, Dict, ClassVar
from django.core.exceptions import ValidationError
from jsonschema import validate, ValidationError as SchemaValidationError


class Phases(enum.Enum):
    MENSTRUAL = 0
    FOLLICULAR = 1
    OVULATION = 2
    LUTEAL = 3
    
    @classmethod
    def phase_to_string(cls, phase) -> str:
        """Get string representation for a phase value."""
        mapping = {
            cls.MENSTRUAL: "Menstrual",
            cls.FOLLICULAR: "Follicular",
            cls.OVULATION: "Ovulation",
            cls.LUTEAL: "Luteal"
        }
        return mapping.get(phase, "Unknown")
    
    @classmethod
    def string_to_phase(cls, phase_str: str) -> Optional[int]:
        """Get enum value from a string (case-insensitive)."""
        if not phase_str or not isinstance(phase_str, str):
            return None
            
        mapping = {
            "menstrual": cls.MENSTRUAL,
            "follicular": cls.FOLLICULAR,
            "ovulation": cls.OVULATION,
            "luteal": cls.LUTEAL
        }
        return mapping.get(phase_str.lower())
        
    def convert_to_string(self, phase) -> str:
        """Convert a phase enum value to its string representation."""
        return self.phase_to_string(phase)
        
    def convert_to_enum(self, phase: str) -> Optional[int]:
        """
        Convert a string to its corresponding phase enum value.
        Case-insensitive matching.
        """
        return self.string_to_phase(phase)

    
class PhaseDuration(enum.Enum):
    MENSTRUAL = 5  # Average period length is 3-7 days, so 5 is a good estimate
    FOLLICULAR = 9  # Varies widely, but usually lasts 7-10 days after menstruation
    OVULATION = 1  # Ovulation itself lasts about 12-24 hours, but fertile window is longer
    LUTEAL = 14  # Luteal phase is the most consistent, usually 12-14 days

class PeriodRecord(models.Model):
    class Meta:
        db_table = 'period_record'
        
    class Event(enum.Enum):
        START = 1
        END = 2
    
    class CurrentStatus(enum.Enum):
        ONGOING = 1
        COMPLETED = 2 
        
    period_record_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id_hash = models.CharField(max_length=200)
    current_status = enum.EnumField(CurrentStatus, default=CurrentStatus.ONGOING)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    
class CurrentPeriod(models.Model):
    class Meta:
        db_table = 'current_period'
        
    user_id_hash = models.CharField(max_length=200, primary_key=True, editable=False)
    current_period_record_id = models.CharField(max_length=200, null=True, blank=True)
    last_period_record_id = models.CharField(max_length=200, null=True, blank=True)
    
class SymptomsRecord(models.Model):
    class Meta:
        db_table = 'symptoms_record'
        
    class SymptomOccurence(enum.Enum):
        DURING_PERIOD = 1
        NON_CYCLE_PHASE = 2
    
    symptom_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id_hash = models.CharField(max_length=200)
    symptom = models.CharField(max_length=200)
    comments = models.TextField()
    symptom_occurence = enum.EnumField(SymptomOccurence)
    period_record_id = models.CharField(max_length=200, null=True, blank=True)
    created_datetime = models.DateTimeField(auto_now_add=True)


class PhaseInfo(models.Model):

    class Meta:
        db_table = 'cycle_phase'
    
    phase_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    phase_type = enum.EnumField(Phases)
    name = models.CharField(max_length=100)
    days_in_cycle = models.CharField(max_length=200)
    hormone_changes = models.TextField()
    common_symptoms = models.JSONField()  # Store as a JSON array
    description = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
class ExerciseDetails(models.Model):
    
    class Meta:
        db_table = 'exercise_details'
    
    detail_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    phase = enum.EnumField(Phases)
    name = models.CharField(max_length=100)
    description = models.TextField()
    benefits_during_phase = models.TextField()
    difficulty = models.CharField(max_length=50)
    duration = models.CharField(max_length=50)
    modifications = models.TextField()  

    
class LifestyleAdjustment(models.Model):

    class Meta:
        db_table = 'lifestyle_adjustment'
    
    adjustment_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    phase = enum.EnumField(Phases)
    work = models.JSONField()
    social = models.JSONField()
    relationships = models.JSONField()   


class HealthWarning(models.Model):

    class Meta:
        db_table = 'health_warning'
    
    warning_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    phase = enum.EnumField(Phases)
    when_to_seek_help = models.JSONField()   

    
#################################################################
##################### RECOMMENDATIONS ############################
#################################################################   



# Schema for Nutrition
nutrition_schema = {
    "type": "object",
    "properties": {
        "foods_to_emphasize": {"type": "array", "items": {"type": "string"}},
        "foods_to_minimize": {"type": "array", "items": {"type": "string"}},
        "nutrients_to_focus_on": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["foods_to_emphasize", "foods_to_minimize", "nutrients_to_focus_on"]
}

# Schema for Exercise
exercise_schema = {
    "type": "object",
    "properties": {
        "recommended_types": {"type": "array", "items": {"type": "string"}},
        "intensity_level": {"type": "string"},
        "exercise_to_avoid": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["recommended_types", "intensity_level", "exercise_to_avoid"]
}

# Schema for Self-care
self_care_schema = {
    "type": "object",
    "properties": {
        "physical": {"type": "array", "items": {"type": "string"}},
        "emotional": {"type": "array", "items": {"type": "string"}},
        "sleep": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["physical", "emotional", "sleep"]
}

def validate_nutrition(value):
    try:
        for item in value:
            validate(item, nutrition_schema)
    except SchemaValidationError as e:
        raise ValidationError(f"Invalid nutrition data: {str(e)}")

def validate_exercise(value):
    try:
        for item in value:
            validate(item, exercise_schema)
    except SchemaValidationError as e:
        raise ValidationError(f"Invalid exercise data: {str(e)}")

def validate_self_care(value):
    try:
        for item in value:
            validate(item, self_care_schema)
    except SchemaValidationError as e:
        raise ValidationError(f"Invalid self-care data: {str(e)}")

    
class RecommendationsNutrition(models.Model):
    class Meta:
        abstract = True
        
    foods_to_emphasize = models.JSONField()
    foods_to_minimize = models.JSONField()
    nutrients_to_focus_on = models.JSONField()
    

class RecommendationsExercise(models.Model):
    class Meta:
        abstract = True
        
    recommended_types = models.JSONField()
    intensity_level = models.CharField(max_length=50)
    exercise_to_avoid = models.JSONField()
    

class RecommendationsSelfCare(models.Model):
    class Meta:
        abstract = True
        
    physical = models.JSONField()
    emotional = models.JSONField()
    sleep = models.JSONField()
    
    
class Recommendations(models.Model):
    
    class Meta:
        db_table = 'recommendations'
    
    recommendation_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    phase = enum.EnumField(Phases)
    nutrition = models.JSONField(
        default=list,
        validators=[validate_nutrition]
    )
    exercise = models.JSONField(
        default=list,
        validators=[validate_exercise]
    )
    self_care = models.JSONField(
        default=list,
        validators=[validate_self_care]
    )

#################################################################
##################### NUTRIENT DETAILS ##########################
#################################################################


key_nutrient_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "nutrient": {"type": "string"},
            "benefits_during_phase": {"type": "string"},
            "food_sources": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["nutrient", "benefits_during_phase", "food_sources"]
    }
}

# Validator for key_nutrient JSON
def validate_key_nutrient(value):
    try:
        validate(value, key_nutrient_schema)
    except SchemaValidationError as e:
        raise ValidationError(f"Invalid key_nutrient data: {str(e)}")

class NutrientDetailsKeyNutrient(models.Model):
    
    class Meta:
        abstract = True
    
    nutrient = models.CharField(max_length=100)
    benefits_during_phase = models.TextField()
    food_sources = models.JSONField()

    
class NutrientDetails(models.Model):   
    
    class Meta:
        db_table = 'nutrient_details' 
    
    detail_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    phase = enum.EnumField(Phases)
    key_nutrient = models.JSONField(
        default=list,
        validators=[validate_key_nutrient]
    )
    meal_plan = models.JSONField()
    hydration_tips = models.TextField()
    supplement_recommendations = models.JSONField()


