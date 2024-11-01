from pathlib import Path
from traceback import print_exc
from joblib import load as joblib_load
from rest_framework.views import APIView
from rest_framework import status
from django.utils.decorators import method_decorator

from utils.helpers import format_response, get_serialized_data
from predictions.models import CycleStatPrediction, PeriodPredictions
from predictions.serializers import CreateCycleStatPredictionSerializer, CreatePredictionSerializer
from predictions.utils import get_average_cycle_length, get_period_statistics, predict_next_period_start


class CreatePredictionView(APIView):
    create_prediction_serializer = CreatePredictionSerializer
    
    @format_response
    def post(self, request):
        request_body = self.create_prediction_serializer(data=request.data)
        request_body.is_valid(raise_exception=True)           

        user_id_hash = get_serialized_data(request_body, 'user_id_hash')
        user_data = get_serialized_data(request_body, 'user_data')
        
        features = [
            user_data['CycleNumber'],
            user_data['LengthofCycle'],
            user_data['LengthofLutealPhase'],
            user_data['TotalNumberofHighDays'],
            user_data['TotalNumberofPeakDays'],
            user_data['UnusualBleeding'],
            user_data['PhasesBleeding'],
            user_data['IntercourseInFertileWindow'],
            user_data['Age'],
            user_data['BMI'],
            user_data['Method']
        ]
        
        model_path = Path(__file__).resolve().parents[2] / 'DecisionTreeForOvulationDayPrediction.pkl'
        model = joblib_load(model_path)
        
        prediction_data = model.predict([features])
        
        period_prediction = PeriodPredictions.objects.create(
            user_id_hash=user_id_hash,
            user_data=user_data,
            prediction_data=prediction_data
        )
        period_prediction.save()
        
        response_body = {
            "user_data": user_data,
            "prediction_data": prediction_data
        }

        return response_body


class CreateCycleStatPredictionView(APIView):
    create_cycle_stat_prediction_serializer = CreateCycleStatPredictionSerializer

    @format_response
    def post(self, request):
        request_body = self.create_cycle_stat_prediction_serializer(data=request.data)
        request_body.is_valid(raise_exception=True) 
        
        user_id_hash = get_serialized_data(request_body, 'user_id_hash')
        
        average_cycle_length = get_average_cycle_length(user_id_hash)
        period_statistics = get_period_statistics(user_id_hash)
        next_period_prediction = predict_next_period_start(user_id_hash)

        cycle_stat_prediction = CycleStatPrediction.objects.create(
            user_id_hash=user_id_hash,
            average_cycle_length=average_cycle_length,
            period_statistics=period_statistics,
            next_period_prediction=next_period_prediction
        )
        
        response_body = {
            'average_cycle_length': average_cycle_length,
            'period_statistics': period_statistics,
            'next_period_prediction': next_period_prediction
        }

        return response_body

