from django.db.models import Avg
from django.utils import timezone
import numpy as np
from scipy.stats import norm

from cycles.models import PeriodRecord

def calculate_cycle_lengths(user_id_hash):
    periods = PeriodRecord.objects.filter(user_id_hash=user_id_hash, current_status=PeriodRecord.CurrentStatus.COMPLETED.value).order_by('start_datetime')
    cycle_lengths = []
    for i in range(len(periods)-1):
        cycle_length = (periods[i+1].start_datetime - periods[i].start_datetime).days
        cycle_lengths.append(cycle_length)
    return cycle_lengths

def get_average_cycle_length(user_id_hash):
    cycle_lengths = calculate_cycle_lengths(user_id_hash)
    if cycle_lengths:
        return np.mean(cycle_lengths)
    return None

def get_period_statistics(user_id_hash):
    cycle_lengths = calculate_cycle_lengths(user_id_hash)
    if cycle_lengths:
        average_cycle_length = np.mean(cycle_lengths)
        std_dev_cycle_length = np.std(cycle_lengths)
        median_cycle_length = np.median(cycle_lengths)
        
        return {
            'average_cycle_length': average_cycle_length,
            'std_dev_cycle_length': std_dev_cycle_length,
            'median_cycle_length': median_cycle_length
        }
    return None

def predict_next_period_start(user_id_hash):
    cycle_lengths = calculate_cycle_lengths(user_id_hash)
    if cycle_lengths:
        # Assuming a normal distribution of cycle lengths
        avg_cycle_length = np.mean(cycle_lengths)
        std_dev_cycle_length = np.std(cycle_lengths)
        # Predict next period start date based on average cycle length
        next_period_start_date = timezone.now() + timezone.timedelta(days=avg_cycle_length)
        # Calculate the probability of period starting within 7 days of the predicted date
        prob_within_7_days = norm.cdf(7, avg_cycle_length, std_dev_cycle_length)
        
        return {
            'next_period_start_date': next_period_start_date,
            'probability_within_7_days': prob_within_7_days
        }
    return None
