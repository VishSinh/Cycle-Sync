# Generated by Django 4.1.13 on 2025-03-21 06:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('predictions', '0002_delete_cyclestatprediction_delete_periodpredictions'),
    ]

    operations = [
        migrations.CreateModel(
            name='CyclePreditction',
            fields=[
                ('user_id_hash', models.CharField(editable=False, max_length=200, primary_key=True, serialize=False)),
                ('cycle_length', models.IntegerField()),
                ('period_duration', models.IntegerField()),
                ('next_period_start', models.DateTimeField()),
                ('next_period_end', models.DateTimeField()),
                ('days_until_next_period', models.IntegerField()),
                ('update_datetime', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
