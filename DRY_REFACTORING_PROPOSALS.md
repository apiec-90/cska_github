# DRY Refactoring Proposals

## 🎯 Обнаруженные паттерны дублирования

### 1. **Дублирование в Views - Контексты и объекты**

#### Проблема:
Идентичные паттерны создания контекста в `athletes/`, `attendance/`, `payments/` views:

```python
# athletes/views.py
context = {
    'title': 'Спортсмены',
    'athletes': athletes,
}

# attendance/views.py  
context = {
    'title': 'Посещаемость',
    'attendance_records': attendance_records,
}

# payments/views.py
context = {
    'title': 'Оплаты', 
    'payments': payments,
}
```

#### Решение:
Создать базовый класс `BaseListView` в `core/views/base.py`:

```python
from django.shortcuts import render
from typing import Dict, Any, Optional

class BaseListView:
    """Базовый класс для list views с оптимизацией запросов"""
    
    template_name: str = None
    context_object_name: str = None
    title: str = None
    model = None
    select_related_fields: list = []
    prefetch_related_fields: list = []
    ordering: list = []
    
    def get_queryset(self):
        """Получить оптимизированный queryset"""
        qs = self.model.objects.all()
        
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        
        if self.prefetch_related_fields:
            qs = qs.prefetch_related(*self.prefetch_related_fields)
            
        if self.ordering:
            qs = qs.order_by(*self.ordering)
            
        return qs
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Создать стандартный контекст"""
        context = {
            'title': self.title,
            self.context_object_name: self.get_queryset(),
        }
        context.update(kwargs)
        return context
    
    def render(self, request):
        """Отрендерить шаблон"""
        context = self.get_context_data()
        return render(request, self.template_name, context)
```

Использование:
```python
# athletes/views.py
class AthleteListView(BaseListView):
    model = Athlete
    template_name = 'athletes/list.html'
    context_object_name = 'athletes'
    title = 'Спортсмены'
    select_related_fields = ['user']
    ordering = ['last_name', 'first_name']

def list_athletes(request):
    return AthleteListView().render(request)
```

### 2. **Дублирование в Views - get_object_or_404 с select_related**

#### Проблема:
Повторяющиеся паттерны получения объектов:

```python
# attendance/views.py
attendance = get_object_or_404(Attendance.objects.select_related('athlete__user'), pk=pk)

# payments/views.py  
payment = get_object_or_404(Payment.objects.select_related('athlete__user'), pk=pk)

# athletes/views.py
athlete = get_object_or_404(Athlete.objects.select_related('user'), pk=pk)
```

#### Решение:
Создать утилитную функцию в `core/utils/views.py`:

```python
from django.shortcuts import get_object_or_404
from typing import Type, Any, List

def get_optimized_object_or_404(
    model: Type, 
    pk: Any, 
    select_related: List[str] = None,
    prefetch_related: List[str] = None
):
    """Получить объект с оптимизированными запросами или 404"""
    qs = model.objects.all()
    
    if select_related:
        qs = qs.select_related(*select_related)
    
    if prefetch_related:
        qs = qs.prefetch_related(*prefetch_related)
    
    return get_object_or_404(qs, pk=pk)
```

Использование:
```python
from core.utils.views import get_optimized_object_or_404

# attendance/views.py
attendance = get_optimized_object_or_404(
    Attendance, pk, select_related=['athlete__user']
)

# payments/views.py
payment = get_optimized_object_or_404(
    Payment, pk, select_related=['athlete__user']
)
```

### 3. **Дублирование в Admin - get_queryset методы**

#### Проблема:
Идентичные паттерны оптимизации в админке:

```python
# core/admin/user_admins.py
def get_queryset(self, request):
    """Оптимизация запросов"""
    qs = super().get_queryset(request)
    return qs.select_related('user')

# athletes/admin.py  
def get_queryset(self, request):
    """Оптимизация: предзагружаем группу для столбца group."""
    qs = super().get_queryset(request)
    return qs.select_related('group')
```

#### Решение:
Создать миксин в `core/admin/mixins.py`:

```python
from typing import List

class OptimizedQuerysetMixin:
    """Миксин для автоматической оптимизации queryset в админке"""
    
    # Настройки оптимизации (переопределить в наследниках)
    admin_select_related: List[str] = []
    admin_prefetch_related: List[str] = []
    
    def get_queryset(self, request):
        """Автоматически оптимизировать queryset"""
        qs = super().get_queryset(request)
        
        if self.admin_select_related:
            qs = qs.select_related(*self.admin_select_related)
        
        if self.admin_prefetch_related:
            qs = qs.prefetch_related(*self.admin_prefetch_related)
        
        return qs
```

Использование:
```python
from core.admin.mixins import OptimizedQuerysetMixin

@admin.register(Trainer)
class TrainerAdmin(OptimizedQuerysetMixin, BasePersonAdmin):
    admin_select_related = ['user']
    admin_prefetch_related = ['traininggroup_set']
    # остальные настройки...

@admin.register(Athlete)  
class AthleteAdmin(OptimizedQuerysetMixin, admin.ModelAdmin):
    admin_select_related = ['group']
    # остальные настройки...
```

### 4. **Дублирование в Registration - Создание профилей**

#### Проблема:
Повторяющийся код создания профилей в `core/views.py` и `core/admin_registration.py`:

```python
# Повторяется 4 раза для Trainer, Parent, Athlete, Staff
Trainer.objects.create(
    user=draft.user,
    first_name=form.cleaned_data['first_name'],
    last_name=form.cleaned_data['last_name'], 
    phone=form.cleaned_data.get('phone', ''),
    birth_date=form.cleaned_data['birth_date'],
)
```

#### Решение:
Создать фабричную функцию в `core/utils/registration.py`:

```python
from typing import Dict, Any
from .models import Trainer, Parent, Athlete, Staff

ROLE_MODEL_MAP = {
    'trainer': Trainer,
    'parent': Parent, 
    'athlete': Athlete,
    'staff': Staff,
}

def create_profile_from_form(user, role: str, form_data: Dict[str, Any]) -> Any:
    """Создать профиль пользователя по роли из данных формы"""
    model_class = ROLE_MODEL_MAP.get(role)
    if not model_class:
        raise ValueError(f"Unknown role: {role}")
    
    profile_data = {
        'user': user,
        'first_name': form_data['first_name'],
        'last_name': form_data['last_name'],
        'phone': form_data.get('phone', ''),
        'birth_date': form_data['birth_date'],
    }
    
    # Специальные поля для staff
    if role == 'staff':
        profile_data['role'] = 'other'
    
    return model_class.objects.create(**profile_data)

def sync_user_names_from_form(user, form_data: Dict[str, Any]) -> None:
    """Синхронизировать ФИО пользователя с данными формы"""
    user.first_name = form_data['first_name']
    user.last_name = form_data['last_name'] 
    user.save(update_fields=['first_name', 'last_name'])
```

Использование:
```python
from core.utils.registration import create_profile_from_form, sync_user_names_from_form

# core/views.py
if form.is_valid():
    sync_user_names_from_form(draft.user, form.cleaned_data)
    create_profile_from_form(draft.user, draft.role, form.cleaned_data)
    # ... остальная логика
```

## 📊 Ожидаемые результаты

### Количественные улучшения:
- **-120 строк** дублированного кода
- **-8 методов** `get_queryset` с идентичной логикой  
- **-4 блока** создания профилей
- **-12 контекстов** с повторяющейся структурой

### Качественные улучшения:
- ✅ **DRY принцип** - устранение дублирования
- ✅ **Единая точка изменений** - легче поддерживать
- ✅ **Консистентность** - одинаковое поведение везде
- ✅ **Типизация** - лучшая поддержка IDE
- ✅ **Тестируемость** - проще покрыть тестами

## 🚨 Риски и ограничения

### Низкий риск:
- Все изменения **обратно совместимы**
- Не меняют **публичные API**
- Не затрагивают **модели и миграции**
- Не влияют на **внешний вид** админки

### Требуют внимания:
- Тестирование всех views после рефакторинга
- Проверка производительности оптимизированных запросов
- Обновление документации для новых утилит

## 🎯 План внедрения

1. **Фаза 1:** Создать утилиты и миксины
2. **Фаза 2:** Рефакторинг views (по одному приложению)
3. **Фаза 3:** Рефакторинг admin классов  
4. **Фаза 4:** Рефакторинг registration логики
5. **Фаза 5:** Удаление старого дублированного кода

Каждая фаза должна сопровождаться тестированием и может быть отдельным коммитом.
