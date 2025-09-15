from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db.models import Count

from core.models import (
    Athlete, Parent, Trainer, Staff,
    TrainingGroup, AthleteTrainingGroup, AthleteParent,
)


class Command(BaseCommand):
    help = "Аудит целостности данных: пользователи, роли, связи, дубликаты"

    def add_arguments(self, parser):
        parser.add_argument("--fix", action="store_true", help="Попробовать автоматически исправить находки (осторожно)")

    def handle(self, *args, **options):
        fix = options.get("fix", False)
        report = []

        # 1) Пользовательские профили 1:1
        report.append(self._audit_one_to_one("Athlete", Athlete))
        report.append(self._audit_one_to_one("Parent", Parent))
        report.append(self._audit_one_to_one("Trainer", Trainer))
        report.append(self._audit_one_to_one("Staff", Staff))

        # 2) Дубликаты M2M связей
        report.append(self._audit_m2m("AthleteTrainingGroup", AthleteTrainingGroup, ["athlete_id", "training_group_id"], fix))
        report.append(self._audit_m2m("AthleteParent", AthleteParent, ["athlete_id", "parent_id"], fix))

        # 3) Группы Django ↔ роли Staff (минимальная проверка)
        report.append(self._audit_staff_groups(fix))

        # 4) Группы тренеров: trainer -> traininggroup.trainer
        report.append(self._audit_trainer_links())

        # 5) Статистика
        report.append(self._stats())

        # Печать отчета
        self.stdout.write("\n=== АУДИТ ДАННЫХ ===")
        for block in report:
            self.stdout.write(block)

    def _audit_one_to_one(self, name: str, model):
        users_with_profile = set(model.objects.values_list("user_id", flat=True))
        existing_users = set(User.objects.filter(id__in=users_with_profile).values_list("id", flat=True))
        missing_users = users_with_profile - existing_users

        profiles_without_user = model.objects.filter(user__isnull=True).count()

        multi_profiles = (
            model.objects.values("user_id")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .count()
        )

        return (
            f"[OneToOne:{name}] profiles={len(users_with_profile)} missing_users={len(missing_users)} "
            f"profiles_without_user={profiles_without_user} duplicates_per_user={multi_profiles}"
        )

    def _audit_m2m(self, name: str, model, fields, fix: bool):
        dup_qs = (
            model.objects.values(*fields)
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
        )
        dup_count = dup_qs.count()
        if fix and dup_count:
            # Удаляем лишние записи, оставляя по одной
            for row in dup_qs:
                dup_ids = list(
                    model.objects.filter(
                        **{f: row[f] for f in fields}
                    ).values_list("id", flat=True)
                )
                # оставляем минимальный id
                keep = min(dup_ids)
                remove = [i for i in dup_ids if i != keep]
                model.objects.filter(id__in=remove).delete()
        return f"[M2M:{name}] duplicates={dup_count}{' (fixed)' if fix and dup_count else ''}"

    def _audit_staff_groups(self, fix: bool):
        info = []
        managers_group, _ = Group.objects.get_or_create(name="Менеджеры")
        manager_ids = set(
            Staff.objects.filter(role="manager").values_list("user_id", flat=True)
        )
        in_group_ids = set(managers_group.user_set.values_list("id", flat=True))

        missing_in_group = manager_ids - in_group_ids
        extra_in_group = in_group_ids - manager_ids

        if fix:
            if missing_in_group:
                managers_group.user_set.add(*list(User.objects.filter(id__in=missing_in_group)))
            if extra_in_group:
                managers_group.user_set.remove(*list(User.objects.filter(id__in=extra_in_group)))

        info.append(f"missing_in_group={len(missing_in_group)}{' (fixed)' if fix and missing_in_group else ''}")
        info.append(f"extra_in_group={len(extra_in_group)}{' (fixed)' if fix and extra_in_group else ''}")
        return "[Staff↔Group] " + ", ".join(info)

    def _audit_trainer_links(self):
        # Группы без тренера и тренеры без групп (быстрая проверка)
        groups_without_trainer = TrainingGroup.objects.filter(trainer__isnull=True).count()
        trainers_without_groups = Trainer.objects.filter(traininggroup__isnull=True).count()
        return f"[Trainer↔Groups] groups_without_trainer={groups_without_trainer} trainers_without_groups={trainers_without_groups}"

    def _stats(self):
        return (
            f"[Stats] users={User.objects.count()} athletes={Athlete.objects.count()} parents={Parent.objects.count()} "
            f"trainers={Trainer.objects.count()} staff={Staff.objects.count()} groups={TrainingGroup.objects.count()}"
        )


