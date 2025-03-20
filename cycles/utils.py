
from django.utils import timezone

from cycles.models import CurrentPeriod, PeriodRecord, PhaseDuration, Phases

def get_avg_cycle_length(user_id_hash):
    """Returns the average cycle length for the user, or None if not enough data."""
    period_records = PeriodRecord.objects.filter(user_id_hash=user_id_hash).order_by("-start_datetime").values("start_datetime")

    if len(period_records) < 2:
        return None  # Not enough records to calculate cycle length

    cycle_lengths = [
        (period_records[i]["start_datetime"] - period_records[i + 1]["start_datetime"]).days
        for i in range(len(period_records) - 1)
    ]
    

    return int(round(sum(cycle_lengths) / len(cycle_lengths))) if cycle_lengths else None


def get_current_phase(user_id_hash):
    """Determines the current menstrual phase based on the last recorded period."""
    current_period = CurrentPeriod.objects.filter(user_id_hash=user_id_hash).first()
    if not current_period:
        return "Unknown", None

    if current_period.current_period_record_id:
        return Phases.MENSTRUAL, None

    if not current_period.last_period_record_id:
        return "Unknown", None

    last_period = PeriodRecord.objects.filter(period_record_id=current_period.last_period_record_id).first()
    if not last_period:
        return "Unknown", None

    date_of_last_period = last_period.start_datetime
    today = timezone.now()
    cycle_days = (today - date_of_last_period).days

    if cycle_days < PhaseDuration.FOLLICULAR.value:
        return Phases.FOLLICULAR, cycle_days
    elif cycle_days < PhaseDuration.FOLLICULAR.value + PhaseDuration.OVULATION.value:
        return Phases.OVULATION, cycle_days
    else:
        return Phases.LUTEAL, cycle_days


def get_days_until_next_phase(phase, cycle_days, avg_cycle_length):
    """Calculates the number of days until the next menstrual phase."""
    
    if phase == "Unknown" or cycle_days is None:
        return None  # Cannot determine the next phase

    if phase == Phases.FOLLICULAR:
        return max(0, PhaseDuration.FOLLICULAR.value - cycle_days)
    elif phase == Phases.OVULATION:
        return max(0, PhaseDuration.FOLLICULAR.value + PhaseDuration.OVULATION.value - cycle_days)
    elif phase == Phases.LUTEAL:
        return max(0, avg_cycle_length - cycle_days) if avg_cycle_length else None  # Handle None case

    return None


def get_avg_period_length(user_id_hash):
    """Returns the average period length for the user, or None if not enough data."""
    period_records = PeriodRecord.objects.filter(user_id_hash=user_id_hash, current_status=PeriodRecord.CurrentStatus.COMPLETED.value).order_by("-start_datetime").values("start_datetime", "end_datetime")

    if len(period_records) < 2:
        return None  # Not enough records to calculate period length

    period_lengths = [
        (period_records[i]["end_datetime"] - period_records[i]["start_datetime"]).days
        for i in range(len(period_records))
    ]

    return int(round(sum(period_lengths) / len(period_lengths))) if period_lengths else None
