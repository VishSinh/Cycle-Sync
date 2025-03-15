from rest_framework.views import APIView
from logging import getLogger

from cycles.models import PeriodRecord
from utils.helpers import forge
from predictions.utils import PeriodPredictionService

logger = getLogger(__name__)


class PredictionView(APIView):
    
    @forge
    def get(self, request):
        
        user_id_hash = request.user_obj.user_id_hash
        
        period_records = PeriodRecord.objects.filter(user_id_hash=user_id_hash, current_status=PeriodRecord.CurrentStatus.COMPLETED.value)
        
        period_history = []
        for period_record in period_records:
            period_history.append({
                'start': period_record.start_datetime,
                'end': period_record.end_datetime
            })
        
            
        prediction_service = PeriodPredictionService()
        prediction = prediction_service.predict_next_period(period_history)
        
        logger.info(f"Prediction data generated successfully:\n{prediction}")
        
        return {
            "message": "Prediction data generated successfully",
            "prediction_data": prediction
        }


