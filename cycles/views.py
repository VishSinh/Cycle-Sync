from logging import getLogger
from django.utils import timezone
from datetime import datetime, timedelta
from django.forms import model_to_dict
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import Q
from django.utils.decorators import method_decorator

from cycles.models import PeriodRecord, CurrentPeriod, SymptomsRecord
from cycles.serializers import CreatePeriodRecordSerializer, CreateSymptomsRecordSerializer, FetchPeriodRecordDetailsSerializer, FetchSymptomsRecordsSerializer
from utils.helpers import convert_to_utc, forge, get_serialized_data
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
            'period_record_id': symptom_record.period_record_id 
        }
        
        response_body['message'] = 'Symptoms record saved successfully'
        
        return response_body, 201

