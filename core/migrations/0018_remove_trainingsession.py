from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_alter_athlete_avatar'),
    ]

    operations = [
        # Сначала удаляем unique_together, который ссылается на поле session
        migrations.AlterUniqueTogether(
            name='attendancerecord',
            unique_together=set(),
        ),
        # Удаляем поле session из AttendanceRecord перед удалением модели TrainingSession
        migrations.RemoveField(
            model_name='attendancerecord',
            name='session',
        ),
        migrations.DeleteModel(
            name='TrainingSession',
        ),
    ]
