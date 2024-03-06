from django.utils import timezone
from datetime import datetime, timedelta
from django.forms import model_to_dict
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import Q
from django.utils.decorators import method_decorator

from cycles.models import PeriodRecord, CurrentPeriod, SymptomsRecord
from cycles.serializers import CreatePeriodRecordSerializer, CreateSymptomsRecordSerializer, FetchPeriodRecordDetailsSerializer, FetchPeriodRecordsSerializer, FetchSymptomsRecordsSerializer
from period_tracking_BE.helpers.utils import get_serialized_data, response_obj, validate_token
from period_tracking_BE.helpers.exceptions import CustomException


@method_decorator(validate_token, name='post')
class CreatePeriodRecordView(APIView):
    create_period_record_serializer = CreatePeriodRecordSerializer
    
    def post(self, request):
        try:
            request_body = self.create_period_record_serializer(data=request.data)
            
            ########## HANDLE VALIDATION ERROR ##########
            if not request_body.is_valid():
                errors = request_body.errors
                message = "; ".join([errors[key][0] if key == "non_field_errors" else f"{key} - {errors[key][0]}" for key in errors])
                return response_obj(success=False, message=message, status_code=status.HTTP_400_BAD_REQUEST)
            #############################################
            
            user_id_hash = get_serialized_data(request_body, 'user_id_hash')
            event = get_serialized_data(request_body, 'event')
            
            response_body = {}
            
            if event == PeriodRecord.Event.START:
                current_period, created = CurrentPeriod.objects.get_or_create(
                    user_id_hash=user_id_hash,
                    defaults={
                        'current_period_record_id':None,
                        'last_period_record_id':None
                    })
                
                # Check if period has already started
                if current_period.current_period_record_id != None:
                    raise CustomException('Period already started')
                
                period_record = PeriodRecord.objects.create(
                    user_id_hash=user_id_hash,
                    start_datetime=datetime.now()
                )
                
                current_period.current_period_record_id = period_record.period_record_id
                response_body = {
                    'period_record_id': period_record.period_record_id,
                    'current_status': period_record.current_status,
                    'start_datetime': period_record.start_datetime
                }
                
            elif event == PeriodRecord.Event.END:
                current_period = CurrentPeriod.objects.filter(user_id_hash=user_id_hash)
                if len(current_period) == 0:
                    raise CustomException('Period not started')
                
                current_period = current_period[0]
                
                # Check if period is started
                if current_period.current_period_record_id == None:
                    raise CustomException('Period not started')
                
                # Fetch the period record currently ONGOING and update it
                period_record = PeriodRecord.objects.get(period_record_id=current_period.current_period_record_id)
                period_record.end_datetime = datetime.now()
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
            return response_obj(message='Period record saved successfully', data=response_body)
                
        except CustomException as e:
            return response_obj(success=False, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@method_decorator(validate_token, name='post')
class FetchPeriodRecordsView(APIView):
    fetch_period_records_serializer = FetchPeriodRecordsSerializer
    
    def post(self, request):
        try:
            request_body = self.fetch_period_records_serializer(data=request.data)
            
            ########## HANDLE VALIDATION ERROR ##########
            if not request_body.is_valid():
                errors = request_body.errors
                message = "; ".join([errors[key][0] if key == "non_field_errors" else f"{key} - {errors[key][0]}" for key in errors])
                return response_obj(success=False, message=message, status_code=status.HTTP_400_BAD_REQUEST)
            #############################################
            
            user_id_hash = get_serialized_data(request_body, 'user_id_hash')
            page = get_serialized_data(request_body, 'page', 1)
            rows_per_page = get_serialized_data(request_body, 'rows_per_page', 10)
            start_datetime = get_serialized_data(request_body, 'start_datetime', None)
            end_datetime = get_serialized_data(request_body, 'end_datetime', None)
            
            # CASE 1: If both start and end datetime are not provided, fetch all records
            # CASE 2: If start datetime is provided and end datetime is not provided, fetch all records from start datetime to now
            # CASE 3: If end datetime is provided and start datetime is not provided, fetch all records from end datetime to 100 years ago
            # CASE 4: If both start and end datetime are provided, fetch all records between start and end datetime
            start_datetime = timezone.make_aware(datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M:%SZ')) if start_datetime else timezone.now() - timedelta(days=365 * 100)
            end_datetime = timezone.make_aware(datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M:%SZ')) if end_datetime else timezone.now()
            
            # Filter period records based on start and end datetime range
            period_records = PeriodRecord.objects.filter(
                Q(user_id_hash=user_id_hash) &
                (
                    Q(start_datetime__gte=start_datetime, end_datetime__lte=end_datetime) |
                    Q(start_datetime__lte=start_datetime, end_datetime__gte=start_datetime) |
                    Q(start_datetime__lte=end_datetime, end_datetime__gte=end_datetime)
                )
            )
            
            print(period_records)

            # Paginate the period records
            period_records = period_records.order_by('-start_datetime')[(page-1)*rows_per_page:(page)*rows_per_page].values()
            
            print(period_records)
            
            response_body = [
                {
                    'period_record_id': record['period_record_id'],
                    'current_status': record['current_status'],
                    'start_datetime': record['start_datetime'],
                    'end_datetime': record['end_datetime'],
                }
                for record in period_records
            ]

            return response_obj(message='Period records fetched successfully', data=response_body)
        
        except CustomException as e:
            return response_obj(success=False, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(validate_token, name='post')      
class CreateSymptomsRecordView(APIView):
    create_symptoms_record_serializer = CreateSymptomsRecordSerializer
    
    def post(self, request):
        try:
            request_body = self.create_symptoms_record_serializer(data=request.data)
            
            ########## HANDLE VALIDATION ERROR ##########
            if not request_body.is_valid():
                errors = request_body.errors
                message = "; ".join([errors[key][0] if key == "non_field_errors" else f"{key} - {errors[key][0]}" for key in errors])
                return response_obj(success=False, message=message, status_code=status.HTTP_400_BAD_REQUEST)
            #############################################
            
            user_id_hash = get_serialized_data(request_body, 'user_id_hash')
            symptom = get_serialized_data(request_body, 'symptom')
            comments = get_serialized_data(request_body, 'comments', '')
            
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
            return response_obj(message='Symptom record saved successfully', data=response_body)
            
        except CustomException as e:
            return response_obj(success=False, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(validate_token, name='post')       
class FetchSymptomsRecordsView(APIView):
    fetch_symptoms_records_serializer = FetchSymptomsRecordsSerializer
    
    def post(self, request):
        try:
            request_body = self.fetch_symptoms_records_serializer(data=request.data)
            
            ########## HANDLE VALIDATION ERROR ##########
            if not request_body.is_valid():
                errors = request_body.errors
                message = "; ".join([errors[key][0] if key == "non_field_errors" else f"{key} - {errors[key][0]}" for key in errors])
                return response_obj(success=False, message=message, status_code=status.HTTP_400_BAD_REQUEST)
            #############################################
            
            user_id_hash = get_serialized_data(request_body, 'user_id_hash')
            page = get_serialized_data(request_body, 'page', 0)
            rows_per_page = get_serialized_data(request_body, 'rows_per_page', 10)
            symptom_occurence = get_serialized_data(request_body, 'symptom_occurence', 0)
            create_datetime_start = get_serialized_data(request_body, 'create_datetime_start', None)
            create_datetime_end = get_serialized_data(request_body, 'create_datetime_end', None)
            
            # CASE 1: If both start and end datetime are not provided, fetch all records
            # CASE 2: If start datetime is provided and end datetime is not provided, fetch all records from start datetime to now
            # CASE 3: If end datetime is provided and start datetime is not provided, fetch all records from end datetime to 100 years ago
            # CASE 4: If both start and end datetime are provided, fetch all records between start and end datetime
            create_datetime_start = timezone.make_aware(datetime.strptime(create_datetime_start, '%Y-%m-%dT%H:%M:%SZ')) if create_datetime_start else timezone.now() - timedelta(days=365 * 100)
            create_datetime_end = timezone.make_aware(datetime.strptime(create_datetime_end, '%Y-%m-%dT%H:%M:%SZ')) if create_datetime_end else timezone.now()
            
            # Filter symptoms records based on created_datetime range
            symptoms_records = SymptomsRecord.objects.filter(created_datetime__gte=create_datetime_start, created_datetime__lte=create_datetime_end)
            
            # Filter by symptom occurence, if not provided, fetch all records
            if symptom_occurence == SymptomsRecord.SymptomOccurence.DURING_PERIOD:
                symptoms_records = symptoms_records.filter(symptom_occurence=SymptomsRecord.SymptomOccurence.DURING_PERIOD)
            elif symptom_occurence == SymptomsRecord.SymptomOccurence.NON_CYCLE_PHASE:
                symptoms_records = symptoms_records.filter(symptom_occurence=SymptomsRecord.SymptomOccurence.NON_CYCLE_PHASE)
            
            # Paginate the symptoms records
            symptoms_records=symptoms_records.order_by('-created_datetime')[(page-1)*rows_per_page:(page)*rows_per_page].values()
            
            response_body = [
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

            return response_obj(message='Symptoms records fetched successfully', data=response_body)
        
        except CustomException as e:
            return response_obj(success=False, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@method_decorator(validate_token, name='post')  
class FetchPeriodRecordDetailsView(APIView):
    fetch_period_record_detail_serializer = FetchPeriodRecordDetailsSerializer
    
    def post(self, request):
        try:
            request_body = self.fetch_period_record_detail_serializer(data=request.data)
            
            ########## HANDLE VALIDATION ERROR ##########
            if not request_body.is_valid():
                errors = request_body.errors
                message = "; ".join([errors[key][0] if key == "non_field_errors" else f"{key} - {errors[key][0]}" for key in errors])
                return response_obj(success=False, message=message, status_code=status.HTTP_400_BAD_REQUEST)
            #############################################
            
            user_id_hash = get_serialized_data(request_body, 'user_id_hash')
            period_record_id = get_serialized_data(request_body, 'period_record_id')
            
            period_record = PeriodRecord.objects.get(period_record_id=period_record_id)
            if not period_record:
                raise CustomException('Period record not found')
            
            period_record = {
                'period_record_id': period_record.period_record_id,
                'current_status': period_record.current_status,
                'start_datetime': period_record.start_datetime,
                'end_datetime': period_record.end_datetime
            }
            
            symptoms_records = SymptomsRecord.objects.filter(period_record_id=period_record_id).values()
            for symptom in symptoms_records:
                symptom.pop('user_id_hash')
                symptom.pop('period_record_id')
                
            response_body = period_record
            response_body['symptoms_records'] = symptoms_records
                
            return response_obj(message='Period record details fetched successfully', data=response_body)
        
        except CustomException as e:
            return response_obj(success=False, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)