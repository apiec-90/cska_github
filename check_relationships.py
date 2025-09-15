#!/usr/bin/env python
"""
Проверка связей между данными
"""
import os
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def check_relationships():
    """Проверка связей между данными"""
    from core.models import Athlete, Parent, TrainingGroup, AthleteParent, AthleteTrainingGroup
    
    print("🔍 Проверка связей между данными...")
    
    try:
        # Проверяем связи спортсменов с родителями
        athlete_parent_count = AthleteParent.objects.count()
        print(f"📊 Связей спортсмен-родитель: {athlete_parent_count}")
        
        if athlete_parent_count > 0:
            print("👨‍👩‍👧‍👦 Связи спортсмен-родитель:")
            for rel in AthleteParent.objects.all()[:5]:
                print(f"  - {rel.athlete} ↔ {rel.parent}")
        
        # Проверяем связи спортсменов с группами
        athlete_group_count = AthleteTrainingGroup.objects.count()
        print(f"📊 Связей спортсмен-группа: {athlete_group_count}")
        
        if athlete_group_count > 0:
            print("🏃 Связи спортсмен-группа:")
            for rel in AthleteTrainingGroup.objects.all()[:5]:
                print(f"  - {rel.athlete} ↔ {rel.training_group}")
        
        # Проверяем группы и их спортсменов
        print(f"\n🏃 Группы и их спортсмены:")
        for group in TrainingGroup.objects.all():
            athletes_in_group = group.athletetraininggroup_set.count()
            print(f"  - {group.name}: {athletes_in_group} спортсменов")
            
            if athletes_in_group > 0:
                for rel in group.athletetraininggroup_set.all()[:3]:
                    print(f"    * {rel.athlete}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки связей: {e}")
        return False

if __name__ == "__main__":
    check_relationships()
