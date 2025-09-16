import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

from django.contrib.auth.models import User  # noqa: E402
from core.models import Athlete, Parent, Trainer, Staff  # noqa: E402

# Check current state
print("=== CURRENT DATABASE STATE ===")
print(f"Total users: {User.objects.count()}")
print(f"Athletes: {Athlete.objects.count()}")  
print(f"Parents: {Parent.objects.count()}")
print(f"Trainers: {Trainer.objects.count()}")
print(f"Staff: {Staff.objects.count()}")

print("\n=== USERS WITH GROUPS ===")
for user in User.objects.all():
    groups = [g.name for g in user.groups.all()]
    print(f"{user.username}: {groups}")

print("\n=== PROFILE MATCHES ===")
mismatches = []

# Check athletes
for user in User.objects.filter(groups__name='Спортсмены'):
    if not Athlete.objects.filter(user=user).exists():
        mismatches.append(f"User {user.username} in 'Спортсмены' but no Athlete profile")

for athlete in Athlete.objects.all():
    if not athlete.user.groups.filter(name='Спортсмены').exists():
        mismatches.append(f"Athlete {athlete.user.username} has no 'Спортсмены' group")

# Check parents  
for user in User.objects.filter(groups__name='Родители'):
    if not Parent.objects.filter(user=user).exists():
        mismatches.append(f"User {user.username} in 'Родители' but no Parent profile")

for parent in Parent.objects.all():
    if not parent.user.groups.filter(name='Родители').exists():
        mismatches.append(f"Parent {parent.user.username} has no 'Родители' group")

# Check trainers
for user in User.objects.filter(groups__name='Тренеры'):
    if not Trainer.objects.filter(user=user).exists():
        mismatches.append(f"User {user.username} in 'Тренеры' but no Trainer profile")

for trainer in Trainer.objects.all():
    if not trainer.user.groups.filter(name='Тренеры').exists():
        mismatches.append(f"Trainer {trainer.user.username} has no 'Тренеры' group")

# Check staff
for user in User.objects.filter(groups__name='Сотрудники'):
    if not Staff.objects.filter(user=user).exists():
        mismatches.append(f"User {user.username} in 'Сотрудники' but no Staff profile")

for staff in Staff.objects.all():
    if not staff.user.groups.filter(name='Сотрудники').exists():
        mismatches.append(f"Staff {staff.user.username} has no 'Сотрудники' group")

if mismatches:
    print(f"\n❌ FOUND {len(mismatches)} MISMATCHES:")
    for mismatch in mismatches:
        print(f"  - {mismatch}")
else:
    print("\n✅ NO MISMATCHES FOUND")

print("\n=== EXPECTED TEST USERS ===")
expected_users = [
    'athlete1', 'athlete2', 'athlete3', 'athlete4', 'athlete5',
    'parent1', 'parent2', 'parent3', 
    'trainer1', 'trainer2', 'trainer3',
    'staff_manager'
]

print("Missing test users:")
for username in expected_users:
    if not User.objects.filter(username=username).exists():
        print(f"  - {username}")