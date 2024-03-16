from celery import shared_task
from datetime import datetime, timedelta
from cycles.models import PeriodRecord, CurrentPeriod

@shared_task
def update_period_records():
    try:
        threshold_datetime = datetime.now() - timedelta(days=7)
        
        # Get all the ongoing period records which have not been updated for more than 7 days
        records_to_update = PeriodRecord.objects.filter(
            current_status=PeriodRecord.CurrentStatus.ONGOING,
            start_datetime__lte=threshold_datetime,
            end_datetime=None
        )
        
        # Update the end_datetime for the records
        for record in records_to_update:
            record.end_datetime = datetime.now()
            record.save()
            
            user_id_hash = record.user_id_hash
            
            # Update the current period record for the user
            current_period = CurrentPeriod.objects.get(user_id_hash=user_id_hash)
            
            current_period.current_period_record_id = None
            current_period.last_period_record_id = record.period_record_id
            current_period.save()
            
    except Exception as e:
        print(e)
        pass
