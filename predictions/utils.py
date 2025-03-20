import pickle
import numpy as np
import tensorflow as tf
from datetime import datetime, timedelta
from django.utils import timezone
from logging import getLogger

from cycles.models import PeriodRecord

logger = getLogger(__name__)

class PeriodPredictionService:
    """Service to load the model and make predictions for users"""
    
    def __init__(self, model_path="./models/lstm_combined_model.keras", 
                feature_scaler_path="./models/feature_scaler.pkl", 
                label_scaler_path="./models/label_scaler.pkl"):
        """Load the model and scalers"""
        # Load the model
        self.model = tf.keras.models.load_model(model_path)
        
        # Load the scalers
        with open(feature_scaler_path, 'rb') as f:
            self.feature_scaler = pickle.load(f)
            
        with open(label_scaler_path, 'rb') as f:
            self.label_scaler = pickle.load(f)
    
    def prepare_input_from_history(self, period_history):
        """
        Prepare model input from period start/end dates
        
        Args:
            period_history: List of dictionaries with 'start' and 'end' dates
                            Minimum 4 periods needed (to calculate 3 cycles + current)
        
        Returns:
            last_three_cycles: Array of cycle lengths and period durations
            last_period_date: Date of most recent period
        """
        # Need at least 4 periods to calculate 3 cycles
        if len(period_history) < 4:
            raise ValueError("Need at least 4 periods to make a prediction")
        
        # Convert string dates to datetime objects if needed
        for period in period_history:
            if isinstance(period['start'], str):
                period['start'] = datetime.fromisoformat(period['start'])
            if isinstance(period['end'], str):
                period['end'] = datetime.fromisoformat(period['end'])
        
        # Sort history by start date (most recent last)
        period_history.sort(key=lambda x: x['start'])
        
        # Get most recent periods (last 4)
        recent_periods = period_history[-4:]
        
        # Calculate cycle lengths and period durations
        cycles = []
        
        for i in range(len(recent_periods)-1):
            # Current period
            current = recent_periods[i]
            # Next period
            next_period = recent_periods[i+1]
            
            # Calculate period duration (end - start)
            period_duration = (current['end'] - current['start']).days
            
            # Calculate cycle length (next start - this start)
            cycle_length = (next_period['start'] - current['start']).days
            
            cycles.append([cycle_length, period_duration])
        
        # Get the last period date
        last_period_date = recent_periods[-1]['start']
        
        return cycles, last_period_date
    
    def predict_next_period(self, period_history):
        """
        Predict the next period based on user history
        
        Args:
            period_history: List of dictionaries with 'start' and 'end' dates as datetime objects
            
        Returns:
            dict with prediction details
        """
        try:
            # Prepare input from period history
            
            
            last_three_cycles, last_period_date = self.prepare_input_from_history(period_history)
            logger.info(f"Last three cycles: {last_three_cycles}")
            # Make prediction
            input_data = np.array([last_three_cycles])
            input_flat = input_data.reshape(-1, 2)
            
            # Scale the input
            input_scaled_flat = self.feature_scaler.transform(input_flat)
            input_scaled = input_scaled_flat.reshape(1, 3, 2)
            
            # Get prediction
            prediction_scaled = self.model.predict(input_scaled, verbose=0)
            prediction = self.label_scaler.inverse_transform(prediction_scaled)[0]
            
            # Sanitize prediction
            next_cycle_length = max(min(round(prediction[0]), 45), 21)
            next_period_duration = max(min(round(prediction[1]), 10), 2)
            
            # Calculate next period dates
            next_period_start = last_period_date + timedelta(days=next_cycle_length)
            next_period_end = next_period_start + timedelta(days=next_period_duration)
            
            logger.info(f"Next period start: {next_period_start}, end: {next_period_end}")
            
            # Return prediction details
            return {
                'cycle_length': next_cycle_length,
                'period_duration': next_period_duration,
                'next_period_start': next_period_start,
                'next_period_end': next_period_end,
                'days_until_next_period': (next_period_start - timezone.now()).days
            }
            
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            return None
        
        
def get_next_period_start_date(user_id_hash):
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
    return prediction['next_period_start'] if prediction else None