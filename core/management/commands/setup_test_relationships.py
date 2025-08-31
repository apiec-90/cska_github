from django.core.management.base import BaseCommand
from core.models import TrainingGroup, Athlete, Trainer, AthleteTrainingGroup, GroupSchedule
from django.contrib.auth.models import User
from datetime import time

class Command(BaseCommand):
    help = 'Setup test relationships between groups, athletes and trainers'

    def handle(self, *args, **options):
        # Check current data
        groups = list(TrainingGroup.objects.all())
        athletes = list(Athlete.objects.all())
        trainers = list(Trainer.objects.all())

        self.stdout.write(f"Groups: {len(groups)}")
        self.stdout.write(f"Athletes: {len(athletes)}")
        self.stdout.write(f"Trainers: {len(trainers)}")

        if not groups:
            self.stdout.write("No groups found. Creating test data...")
            # Create test trainer if none exist
            if not trainers:
                user = User.objects.create_user(
                    username='trainer_test',
                    first_name='Тестовый',
                    last_name='Тренер'
                )
                trainer = Trainer.objects.create(
                    user=user,
                    first_name='Тестовый',
                    last_name='Тренер',
                    phone='+7-999-123-45-67'
                )
                trainers.append(trainer)

            # Create test group
            group = TrainingGroup.objects.create(
                name='Младшая группа',
                trainer=trainers[0] if trainers else None,
                age_min=6,
                age_max=12,
                max_athletes=15,
                is_active=True
            )
            groups.append(group)

        # Assign trainers to groups without trainers
        for group in groups:
            if not group.trainer and trainers:
                group.trainer = trainers[0]
                group.save()
                self.stdout.write(f"Assigned trainer {trainers[0]} to group {group.name}")

        # Add athletes to groups
        for i, athlete in enumerate(athletes):
            # Distribute athletes across groups
            group = groups[i % len(groups)]
            
            # Check if relationship already exists
            relation, created = AthleteTrainingGroup.objects.get_or_create(
                athlete=athlete,
                training_group=group
            )
            if created:
                self.stdout.write(f"Added {athlete} to group {group.name}")

        # Add schedules to groups
        for group in groups:
            if not group.groupschedule_set.exists():
                # Add Monday and Wednesday schedule
                GroupSchedule.objects.create(
                    training_group=group,
                    weekday=1,  # Monday
                    start_time=time(16, 0),
                    end_time=time(17, 30)
                )
                GroupSchedule.objects.create(
                    training_group=group,
                    weekday=3,  # Wednesday  
                    start_time=time(16, 0),
                    end_time=time(17, 30)
                )
                self.stdout.write(f"Added schedule to group {group.name}")

        # Summary
        for group in groups:
            athletes_count = group.get_athletes_count()
            schedules_count = group.groupschedule_set.count()
            self.stdout.write(
                f"Group: {group.name}, Trainer: {group.trainer}, "
                f"Athletes: {athletes_count}, Schedules: {schedules_count}"
            )

        self.stdout.write(self.style.SUCCESS('Successfully setup test relationships!'))