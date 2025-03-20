import json
from logging import getLogger
from django.conf import settings
from django.forms import model_to_dict
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.views import APIView
from django.db.models import Q
from google import genai

from cycles.models import PeriodRecord, CurrentPeriod, Phases, SymptomsRecord, PhaseInfo, ExerciseDetails, LifestyleAdjustment, NutrientDetails, Recommendations, HealthWarning, Phases
from cycles.serializers import CreatePeriodRecordSerializer, CreateSymptomsRecordSerializer, FetchPeriodRecordDetailsSerializer, FetchSymptomsRecordsSerializer
from cycles.utils import get_avg_cycle_length, get_avg_period_length, get_current_phase, get_days_until_next_phase
from predictions.utils import PeriodPredictionService, get_next_period_start_date
from utils.helpers import convert_to_utc, forge
from utils.exceptions import BadRequest, Conflict, ResourceNotFound

logger = getLogger(__name__)

class PeriodRecordView(APIView):
    
    @forge
    def get(self, request):
        
        user_id_hash = request.user_obj.user_id_hash
        
        period_record_id = request.query_params.get('period_record_id', None)
        page = int(request.query_params.get('page', 1))
        rows_per_page = int(request.query_params.get('rows_per_page', 10))
        start_datetime = request.query_params.get('start_datetime', None)
        end_datetime = request.query_params.get('end_datetime', None)
        
        
        ############################################################################################################
        # Fetch a single period record details
        ############################################################################################################
        if period_record_id:
            if not (period_record:=PeriodRecord.objects.filter(period_record_id=period_record_id).first()):
                raise ResourceNotFound('Period record not found')
            
            symptoms_record_objs = SymptomsRecord.objects.filter(period_record_id=period_record_id).values()
            symptoms_records = [
                {
                    'symptom_id': symptom_record['symptom_id'],
                    'symptom': symptom_record['symptom'],
                    'comments': symptom_record['comments'],
                    'symptom_occurence': symptom_record['symptom_occurence'],
                    'created_datetime': symptom_record['created_datetime']
                }
                for symptom_record in symptoms_record_objs
            ]
            
            response = {
                'message': 'Period record details fetched successfully',
                'period_record_id': period_record.period_record_id,
                'current_status': period_record.current_status,
                'start_datetime': period_record.start_datetime,
                'end_datetime': period_record.end_datetime,
                'symptoms_records': symptoms_records
            }
                
            return response
        
        ############################################################################################################
        # Fetch all period records based on the provided filters
        ############################################################################################################
        
        # CASE 1: If both start and end datetime are not provided, fetch all records
        # CASE 2: If start datetime is provided and end datetime is not provided, fetch all records from start datetime to now
        # CASE 3: If end datetime is provided and start datetime is not provided, fetch all records from end datetime to 100 years ago
        # CASE 4: If both start and end datetime are provided, fetch all records between start and end datetime
        start_datetime = convert_to_utc(start_datetime) if start_datetime else timezone.now() - timedelta(days=365 * 100)
        end_datetime = convert_to_utc(end_datetime) if end_datetime else timezone.now()
        
        # Filter period records based on start and end datetime range
        period_records = PeriodRecord.objects.filter(
            Q(user_id_hash=user_id_hash) &
            (
                Q(start_datetime__lte=end_datetime, end_datetime__gte=start_datetime)
            )
        )


        # Paginate the period records
        period_records = period_records.order_by('-start_datetime')[(page-1)*rows_per_page:(page)*rows_per_page].values()

        period_records = [
            {
                'period_record_id': period_record['period_record_id'],
                'current_status': period_record['current_status'],
                'start_datetime': period_record['start_datetime'],
                'duration_days': (period_record['end_datetime'] - period_record['start_datetime']).days,
                'end_datetime': period_record['end_datetime']
            }
            for period_record in period_records
        ]

        response = {
            "message": "Period records fetched successfully",
            "period_records": period_records
        }
        
        return response
    
    @forge
    def post(self, request):
        
        user_id_hash = request.user_obj.user_id_hash
        
        serializer = CreatePeriodRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        event = serializer.get_value('event')
        date_time = convert_to_utc(serializer.get_value('date_time', timezone.now()))
        
        response_body = {}
        
        if event == PeriodRecord.Event.START:
            current_period, _ = CurrentPeriod.objects.get_or_create(
                user_id_hash=user_id_hash,
                defaults={
                    'current_period_record_id':None,
                    'last_period_record_id':None
                })
            
            # Check if period has already started
            if current_period.current_period_record_id != None:
                raise Conflict('Period already started')
            
            period_record = PeriodRecord.objects.create(
                user_id_hash=user_id_hash,
                start_datetime=date_time,
            )
            
            current_period.current_period_record_id = period_record.period_record_id
            
            response_body = {
                'period_record_id': period_record.period_record_id,
                'current_status': period_record.current_status,
                'start_datetime': period_record.start_datetime
            }
            
        elif event == PeriodRecord.Event.END:
            logger.info("REACHED 0")
            
            current_period = CurrentPeriod.objects.filter(user_id_hash=user_id_hash).first()
            if not current_period:
                raise BadRequest('Period not started')
            
            # Check if period is started
            if current_period.current_period_record_id == None:
                raise BadRequest('Period not started')
            
            # Fetch the period record currently ONGOING and update it
            period_record = PeriodRecord.objects.get(period_record_id=current_period.current_period_record_id)
            period_record.end_datetime = date_time
            period_record.current_status = PeriodRecord.CurrentStatus.COMPLETED
            period_record.save()
            
            # Update the current period record
            current_period.last_period_record_id = period_record.period_record_id
            current_period.current_period_record_id = None
            
            response_body = {
                'period_record_id': period_record.period_record_id,
                'current_status': period_record.current_status,
                'start_datetime': period_record.start_datetime,
                'end_datetime': period_record.end_datetime
            }
            
        current_period.save()
        
        response_body['message'] = 'Period record saved successfully'
        
        return response_body, 201
        
    


class SymptomsRecordView(APIView):
    
    @forge
    def get(self, request):
        
        user_id_hash = request.user_obj.user_id_hash
        
        page = int(request.query_params.get('page', 1))
        rows_per_page = int(request.query_params.get('rows_per_page', 10))
        symptom_occurence = int(request.query_params.get('symptom_occurence', 0))
        start_datetime = request.query_params.get('start_datetime', None)
        end_datetime = request.query_params.get('end_datetime', None)
        
        # CASE 1: If both start and end datetime are not provided, fetch all records
        # CASE 2: If start datetime is provided and end datetime is not provided, fetch all records from start datetime to now
        # CASE 3: If end datetime is provided and start datetime is not provided, fetch all records from end datetime to 100 years ago
        # CASE 4: If both start and end datetime are provided, fetch all records between start and end datetime
        start_datetime = convert_to_utc(start_datetime) if start_datetime else timezone.now() - timedelta(days=365 * 100)
        end_datetime = convert_to_utc(end_datetime) if end_datetime else timezone.now()
        
        # Filter symptoms records based on created_datetime range
        symptoms_records = SymptomsRecord.objects.filter(
            Q(user_id_hash=user_id_hash) &
            Q(created_datetime__gte=start_datetime, created_datetime__lte=end_datetime)
        )
        
        # Filter by symptom occurence, if not provided, fetch all records
        if symptom_occurence == SymptomsRecord.SymptomOccurence.DURING_PERIOD:
            symptoms_records = symptoms_records.filter(symptom_occurence=SymptomsRecord.SymptomOccurence.DURING_PERIOD)
        elif symptom_occurence == SymptomsRecord.SymptomOccurence.NON_CYCLE_PHASE:
            symptoms_records = symptoms_records.filter(symptom_occurence=SymptomsRecord.SymptomOccurence.NON_CYCLE_PHASE)
        
        # Paginate the symptoms records
        symptoms_records=symptoms_records.order_by('-created_datetime')[(page-1)*rows_per_page:(page)*rows_per_page].values()
        
        symptoms = [
            {
                'symptom_id': symptom['symptom_id'],
                'symptom': symptom['symptom'],
                'comments': symptom['comments'],
                'symptom_occurence': symptom['symptom_occurence'],
                'period_record_id': symptom['period_record_id'], 
                'created_datetime': symptom['created_datetime']
            }
            for symptom in symptoms_records
        ]
        response = {
                "message": "Symptoms records fetched successfully",
                "symptoms": symptoms
        }

        return response
    
    @forge
    def post(self, request):
        
        user_id_hash = request.user_obj.user_id_hash
        
        serializer = CreateSymptomsRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        symptom = serializer.get_value('symptom')
        comments = serializer.get_value('comments', '')
        
        current_period, created = CurrentPeriod.objects.get_or_create(
            user_id_hash=user_id_hash,
            defaults={
                'current_period_record_id':None,
                'last_period_record_id':None
            })
        
        symptom_occurence = SymptomsRecord.SymptomOccurence.NON_CYCLE_PHASE if current_period.current_period_record_id == None else SymptomsRecord.SymptomOccurence.DURING_PERIOD
        
        symptom_record = SymptomsRecord.objects.create(
            user_id_hash=user_id_hash,
            symptom=symptom,
            comments=comments,
            symptom_occurence=symptom_occurence
        )
        
        if symptom_occurence == SymptomsRecord.SymptomOccurence.DURING_PERIOD:
            symptom_record.period_record_id = current_period.current_period_record_id
            symptom_record.save()
            
        response_body = {
            'symptom_id': symptom_record.symptom_id,
            'symptom': symptom_record.symptom,
            'comments': symptom_record.comments,
            'symptom_occurence': symptom_record.symptom_occurence,
            'period_record_id': symptom_record.period_record_id ,
            'created_datetime': symptom_record.created_datetime
        }
        
        response_body['message'] = 'Symptoms record saved successfully'
        
        return response_body, 201


class DashboardView(APIView):

    @forge
    def get(self, request):
        user_id_hash = request.user_obj.user_id_hash
        
        current_period = CurrentPeriod.objects.filter(user_id_hash=user_id_hash).first()
        last_period_record_id = current_period.last_period_record_id
        last_period_record = PeriodRecord.objects.filter(period_record_id=last_period_record_id).first()
        last_period_start = last_period_record.start_datetime if last_period_record else None

        avg_cycle_length = get_avg_cycle_length(user_id_hash)
        
        phase, cycle_days = get_current_phase(user_id_hash)
        
        days_until_next_phase = get_days_until_next_phase(phase, cycle_days, avg_cycle_length)
        logger.info(f"Days until next phase: {days_until_next_phase}")
        next_period_start = get_next_period_start_date(user_id_hash)
        
        days_until_next_period = (next_period_start - timezone.now()).days if next_period_start else None

        response = {
            "message": "Dashboard data fetched successfully",
            "last_period_start": last_period_start,
            "avg_cycle_length": avg_cycle_length,
            "current_phase": phase,
            "next_period_start": next_period_start,
            "days_until_next_phase": days_until_next_phase,
            "days_until_next_period": days_until_next_period
        }
        
        return response
    

class DashboardDetailsView(APIView):
    
    @forge
    def get(self, request):
        if not (phase:=request.query_params.get('phase', None)):
            raise BadRequest('Phase not provided')
        
        phase = int(phase)
        
        # Fetch all details for the provided phase
        phase_info = PhaseInfo.objects.filter(phase_type=phase).first()
        exercise_details = ExerciseDetails.objects.filter(phase=phase)
        lifestyle_adjustment = LifestyleAdjustment.objects.filter(phase=phase).first()
        health_warning = HealthWarning.objects.filter(phase=phase).first()
        recommendations = Recommendations.objects.filter(phase=phase).first()
        nutrient_details = NutrientDetails.objects.filter(phase=phase).first()
        
        return {
            "message": "Dashboard details fetched successfully",
            "phase_info": model_to_dict(phase_info) or {},
            "exercise_details": [model_to_dict(exercise) for exercise in exercise_details],
            "lifestyle_adjustments": model_to_dict(lifestyle_adjustment) or {},
            "health_warning": model_to_dict(health_warning) or {},
            "recommendations": model_to_dict(recommendations) or {},
            "nutrient_details": model_to_dict(nutrient_details) or {}
        }
        
        
class CurrentStatusView(APIView):
    
    @forge
    def get(self, request):
        
        user_id_hash = request.user_obj.user_id_hash
        
        current_period = CurrentPeriod.objects.filter(user_id_hash=user_id_hash).first()
        
        if not current_period:
            raise BadRequest('Current period not found')
        
        avg_cycle_length = get_avg_cycle_length(user_id_hash)
        
        avg_period_length = get_avg_period_length(user_id_hash)
        
        next_period_start = get_next_period_start_date(user_id_hash)
        
        response = {
            "message": "Current period status fetched successfully",
            "current_period_record_id": current_period.current_period_record_id,
            "last_period_record_id": current_period.last_period_record_id,
            "avg_cycle_length": avg_cycle_length,
            "avg_period_length": avg_period_length,
            "next_period_start": next_period_start
        }
        
        return response
        
    
 
class GetPhaseDetailsView(APIView):
    
    @forge
    def get(self, request):
        
        if not (phase:=request.query_params.get('phase', None)):
            raise BadRequest('Phase not provided')
        
        phase = int(phase)
        
        # if not (secret_token:=request.query_params.get('secret_token', None)):
        #     raise BadRequest('Secret token not provided')
        
        # secret_token = settings.PHASE_DETAILS_SECRET_TOKEN
        # if secret_token != secret_token:
        #     raise BadRequest('Invalid secret token provided')
        
        if phase == Phases.MENSTRUAL:
            phase = "Menstrual"
        elif phase == Phases.FOLLICULAR:
            phase = "Follicular"
        elif phase == Phases.OVULATION:
            phase = "Ovulation"
        elif phase == Phases.LUTEAL:
            phase = "Luteal"
        else:
            raise BadRequest('Invalid phase provided')
        
        # logger.info(f"{PROMPT}\nThe phase to analyze is: {phase}")
        
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[f"{PROMPT}\nThe phase to analyze is: {phase}"],
        )
        
        # logger.info(f"Response from Gemini API: \n{response}")
        
        raw_text = response.candidates[0].content.parts[0].text

        # Clean and parse the JSON
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(clean_text)
        
        # logger.info(f"Parsed JSON: \n{parsed_json}")
        
        current_phase = parsed_json['current_phase']
        recommendations = parsed_json['recommendations']
        exercise_details = parsed_json['exercise_details']
        nutrition_details = parsed_json['nutrition_details']
        lifestyle_adjustments = parsed_json['lifestyle_adjustments']
        when_to_seek_help = parsed_json['when_to_seek_help']
        
        
        logger.info(f"Current phase: \n{current_phase}")
        logger.info(f"Recommendations: \n{recommendations}")
        logger.info(f"Exercise details: \n{exercise_details}")
        logger.info(f"Nutrition details: \n{nutrition_details}")
        logger.info(f"Lifestyle adjustments: \n{lifestyle_adjustments}")
        logger.info(f"When to seek help: \n{when_to_seek_help}")
        
        
        # Map the phase name to enum value
        phase_mapping = {
            "Menstrual": Phases.MENSTRUAL,
            "Follicular": Phases.FOLLICULAR, 
            "Ovulation": Phases.OVULATION,
            "Luteal": Phases.LUTEAL
        }
        phase_type = phase_mapping[phase]
        
        # Clear existing data for this phase
        logger.info(f"Clearing existing data for phase: {phase} (phase_type={phase_type})")
        PhaseInfo.objects.filter(phase_type=phase_type).delete()
        ExerciseDetails.objects.filter(phase=phase_type).delete()
        LifestyleAdjustment.objects.filter(phase=phase_type).delete()
        HealthWarning.objects.filter(phase=phase_type).delete()
        Recommendations.objects.filter(phase=phase_type).delete()
        NutrientDetails.objects.filter(phase=phase_type).delete()
        
        # Save PhaseInfo
        phase_info = PhaseInfo.objects.create(
            phase_type=phase_type,
            name=current_phase['name'],
            days_in_cycle=current_phase['days_in_cycle'],
            hormone_changes=current_phase['hormone_changes'],
            common_symptoms=current_phase['common_symptoms'],
            description=current_phase['description']
        )
        
        # Save Exercise Details
        exercise_objs = []
        for exercise in exercise_details:
            exercise_obj = ExerciseDetails.objects.create(
                phase=phase_type,
                name=exercise['name'],
                description=exercise['description'],
                benefits_during_phase=exercise['benefits_during_phase'],
                difficulty=exercise['difficulty'],
                duration=exercise['duration'],
                modifications=exercise['modifications']
            )
            exercise_objs.append(exercise_obj)
        
        # Save Lifestyle Adjustments
        lifestyle_obj = LifestyleAdjustment.objects.create(
            phase=phase_type,
            work=lifestyle_adjustments['work'],
            social=lifestyle_adjustments['social'],
            relationships=lifestyle_adjustments['relationships']
        )
        
        # Save Health Warnings
        health_warning = HealthWarning.objects.create(
            phase=phase_type,
            when_to_seek_help=when_to_seek_help
        )
        
        # Create Recommendations objects as dictionaries (not instances of abstract models)
        nutrition_rec = {
            'foods_to_emphasize': recommendations['nutrition']['foods_to_emphasize'],
            'foods_to_minimize': recommendations['nutrition']['foods_to_minimize'],
            'nutrients_to_focus_on': recommendations['nutrition']['nutrients_to_focus_on']
        }
        
        exercise_rec = {
            'recommended_types': recommendations['exercise']['recommended_types'],
            'intensity_level': recommendations['exercise']['intensity_level'],
            'exercise_to_avoid': recommendations['exercise'].get('exercises_to_avoid', [])
        }
        
        self_care_rec = {
            'physical': recommendations['self_care']['physical'],
            'emotional': recommendations['self_care']['emotional'],
            'sleep': recommendations['self_care']['sleep']
        }
        
        # Create and save Recommendations
        recs = Recommendations.objects.create(
            phase=phase_type,
            nutrition=[nutrition_rec],
            exercise=[exercise_rec],
            self_care=[self_care_rec]
        )
        
        # Process key nutrients as dictionaries
        key_nutrients = []
        for nutrient_data in nutrition_details['key_nutrients']:
            key_nutrient = {
                'nutrient': nutrient_data['nutrient'],
                'benefits_during_phase': nutrient_data['benefits_during_phase'],
                'food_sources': nutrient_data['food_sources']
            }
            key_nutrients.append(key_nutrient)
        
        # Create and save Nutrient Details
        nutrient_details_obj = NutrientDetails.objects.create(
            phase=phase_type,
            key_nutrient=key_nutrients,
            meal_plan=nutrition_details['meal_plan'],
            hydration_tips=nutrition_details['hydration_tips'],
            supplement_recommendations=nutrition_details['supplement_recommendations']
        )
        
        response = {
            "message": f"Phase details for {phase} phase fetched and saved successfully",
            # "phase_info": model_to_dict(phase_info),
            # "recommendations": model_to_dict(recs),
            "when_to_seek_help": when_to_seek_help
        }
        
        return response

PROMPT = """
Please provide detailed information about the {PHASE} phase of the menstrual cycle in JSON format.

Return a structured JSON object with the following properties:

{
    "current_phase": {
        "name": "string",
        "days_in_cycle": "string",
        "hormone_changes": "string",
        "common_symptoms": ["array", "of", "symptoms"],
        "description": "string"
    },
    "recommendations": {
        "nutrition": {
            "foods_to_emphasize": ["array", "of", "recommended", "foods"],
            "foods_to_minimize": ["array", "of", "foods", "to", "avoid"],
            "nutrients_to_focus_on": ["array", "of", "key", "nutrients"],
            "meal_ideas": ["array", "of", "meal", "suggestions"]
        },
        "exercise": {
            "recommended_types": ["array", "of", "exercise", "names"],
            "intensity_level": "string",
            "duration_guidelines": "string",
            "exercises_to_avoid": ["array", "of", "exercises", "to", "avoid"]
        },
        "self_care": {
            "physical": ["array", "of", "physical", "self-care", "activities"],
            "emotional": ["array", "of", "emotional", "self-care", "activities"],
            "sleep": ["array", "of", "sleep", "recommendations"]
        }
    },
    "exercise_details": [
        {
            "name": "string",
            "description": "string",
            "benefits_during_phase": "string",
            "difficulty": "easy|medium|hard",
            "duration": "string",
            "modifications": "string"
        }
    ],
    "nutrition_details": {
        "key_nutrients": [
            {
            "nutrient": "string",
            "benefits_during_phase": "string",
            "food_sources": ["array", "of", "sources"]
            }
        ],
        "meal_plan": {
            "breakfast_ideas": ["array", "of", "breakfast", "ideas"],
            "lunch_ideas": ["array", "of", "lunch", "ideas"],
            "dinner_ideas": ["array", "of", "dinner", "ideas"],
            "snack_ideas": ["array", "of", "snack", "ideas"]
        },
        "hydration_tips": "string",
        "supplement_recommendations": ["array", "of", "supplements", "if", "applicable"]
    },
    "lifestyle_adjustments": {
        "work": ["array", "of", "workplace", "adjustments"],
        "social": ["array", "of", "social", "considerations"],
        "relationships": ["array", "of", "relationship", "tips"]
    },
    "when_to_seek_help": ["array", "of", "warning", "signs"]
}
"""