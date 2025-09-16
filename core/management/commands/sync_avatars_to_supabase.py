"""
Django management command для синхронизации аватаров с Supabase Storage
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.utils.supabase_storage import upload_to_supabase_storage, get_supabase_file_url
from core.models import Document, DocumentType


class Command(BaseCommand):
    help = 'Синхронизация локальных аватаров с Supabase Storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет загружено, но не загружать',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Режим просмотра (dry-run)'))
        
        self.stdout.write('🚀 Начинаем синхронизацию аватаров с Supabase Storage...')
        
        # Путь к локальным аватарам
        avatars_path = os.path.join(settings.MEDIA_ROOT, 'avatars')
        
        if not os.path.exists(avatars_path):
            self.stdout.write(self.style.ERROR(f'❌ Папка {avatars_path} не найдена'))
            return
        
        # Получаем все локальные файлы аватаров
        avatar_files = []
        for filename in os.listdir(avatars_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                avatar_files.append(filename)
        
        self.stdout.write(f'📁 Найдено {len(avatar_files)} файлов аватаров')
        
        if not avatar_files:
            self.stdout.write(self.style.SUCCESS('✅ Нет файлов для синхронизации'))
            return
        
        uploaded_count = 0
        error_count = 0
        
        for filename in avatar_files:
            file_path = os.path.join(avatars_path, filename)
            supabase_path = f'avatars/{filename}'
            
            if dry_run:
                self.stdout.write(f'  📋 Будет загружен: {filename} → {supabase_path}')
                continue
            
            try:
                # Читаем файл
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                # Загружаем в Supabase
                success, result = upload_to_supabase_storage(file_data, supabase_path)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ {filename} → Supabase Storage')
                    )
                    uploaded_count += 1
                    
                    # Обновляем записи в базе данных, если они существуют
                    self._update_document_records(filename, result)
                    
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ {filename}: {result}')
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ {filename}: {str(e)}')
                )
                error_count += 1
        
        if not dry_run:
            self.stdout.write('')
            self.stdout.write(f'📊 Результат синхронизации:')
            self.stdout.write(f'  ✅ Загружено: {uploaded_count} файлов')
            self.stdout.write(f'  ❌ Ошибок: {error_count} файлов')
            
            if uploaded_count > 0:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('🎉 Синхронизация завершена!'))
                self.stdout.write('💡 Теперь новые аватары будут автоматически загружаться в Supabase Storage')

    def _update_document_records(self, filename, supabase_url):
        """Обновляем записи Document для аватаров"""
        try:
            avatar_type = DocumentType.objects.get(name='Avatar')
            
            # Ищем документы с локальным путем к этому файлу
            documents = Document.objects.filter(
                document_type=avatar_type,
                file__endswith=filename
            )
            
            for doc in documents:
                # Обновляем путь на Supabase URL
                doc.file = supabase_url
                doc.comment = 'Migrated to Supabase Storage'
                doc.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'    📝 Обновлена запись Document ID {doc.id}')
                )
                
        except DocumentType.DoesNotExist:
            pass  # Avatar type не существует
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'    ⚠️ Не удалось обновить записи для {filename}: {str(e)}')
            )
