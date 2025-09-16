import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Document, DocumentType
from core.utils.supabase_storage import upload_to_supabase_storage, delete_from_supabase_storage
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Синхронизирует локальные документы с Supabase Storage и обновляет записи Document.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Выполнить просмотр без фактической загрузки или удаления файлов.',
        )
        parser.add_argument(
            '--exclude-avatars',
            action='store_true',
            help='Исключить аватары из синхронизации (они уже синхронизированы отдельно).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        exclude_avatars = options['exclude_avatars']
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('🔍 Режим просмотра (dry-run)'))
        
        self.stdout.write(self.style.SUCCESS('🚀 Начинаем синхронизацию документов с Supabase Storage...'))

        # Получаем все документы, которые хранятся локально
        local_docs = Document.objects.filter(file__startswith='documents/')
        
        if exclude_avatars:
            # Исключаем аватары
            try:
                avatar_type = DocumentType.objects.get(name='Avatar')
                local_docs = local_docs.exclude(document_type=avatar_type)
            except DocumentType.DoesNotExist:
                pass
        
        total_docs = local_docs.count()
        self.stdout.write(f'📁 Найдено {total_docs} локальных документов')

        if total_docs == 0:
            self.stdout.write(self.style.WARNING('⚠️ Локальные документы не найдены'))
            return

        uploaded_count = 0
        error_count = 0
        
        for doc in local_docs:
            local_file_path = os.path.join(settings.MEDIA_ROOT, doc.file)
            filename = os.path.basename(doc.file)
            supabase_path = f'documents/{filename}'

            if dry_run:
                self.stdout.write(f'  📋 Будет загружен: {filename} → {supabase_path}')
                continue

            # Проверяем существование локального файла
            if not os.path.exists(local_file_path):
                self.stdout.write(self.style.WARNING(f'  ⚠️ Файл не найден: {local_file_path}'))
                error_count += 1
                continue

            try:
                with open(local_file_path, 'rb') as f:
                    file_data = f.read()
                
                success, result = upload_to_supabase_storage(file_data, supabase_path)

                if success:
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Загружен: {filename}'))
                    uploaded_count += 1
                    
                    # Update Document record
                    doc.file = result  # Store Supabase URL
                    doc.comment = f"{doc.comment} (Migrated to Supabase Storage)" if doc.comment else "Migrated to Supabase Storage"
                    doc.save(update_fields=['file', 'comment'])
                    
                    # Optionally delete local file after successful upload
                    try:
                        os.remove(local_file_path)
                        self.stdout.write(f'  🗑️ Локальный файл удален: {filename}')
                    except Exception as delete_error:
                        self.stdout.write(self.style.WARNING(f'  ⚠️ Не удалось удалить локальный файл: {delete_error}'))
                else:
                    self.stdout.write(self.style.ERROR(f'  ❌ {filename}: Supabase upload error: {result}'))
                    error_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ {filename}: Локальная ошибка: {e}'))
                error_count += 1
        
        self.stdout.write('\n📊 Результат синхронизации:')
        self.stdout.write(self.style.SUCCESS(f'  ✅ Загружено: {uploaded_count} файлов'))
        self.stdout.write(self.style.ERROR(f'  ❌ Ошибок: {error_count} файлов'))

        if error_count == 0:
            self.stdout.write(self.style.SUCCESS('🎉 Все документы успешно синхронизированы с Supabase Storage!'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Некоторые документы не удалось синхронизировать. Проверьте ошибки выше.'))
