#!/usr/bin/env python
import os
import sys
import django
import sqlite3
from pathlib import Path

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def export_to_postgresql():
    """
    Экспортирует всю БД в PostgreSQL SQL файл
    """
    print("🗄️ Экспорт БД в PostgreSQL формат...")
    
    # Подключаемся к SQLite
    db_path = Path(__file__).parent / 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем все таблицы
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = cursor.fetchall()
    
    postgresql_sql = []
    postgresql_sql.append("-- ===========================================")
    postgresql_sql.append("-- ПОЛНАЯ СХЕМА БАЗЫ ДАННЫХ CSKA ДЛЯ POSTGRESQL")
    postgresql_sql.append("-- Включает Django таблицы и кастомные таблицы")
    postgresql_sql.append("-- ===========================================")
    postgresql_sql.append("")
    
    # Группируем таблицы
    django_tables = []
    custom_tables = []
    
    for table in tables:
        table_name = table[0]
        if table_name.startswith('django_') or table_name.startswith('auth_'):
            django_tables.append(table_name)
        else:
            custom_tables.append(table_name)
    
    print(f"🔧 Django таблицы: {len(django_tables)}")
    print(f"🎯 Кастомные таблицы: {len(custom_tables)}")
    
    # Django таблицы
    postgresql_sql.append("-- DJANGO ТАБЛИЦЫ")
    postgresql_sql.append("-- ===========================================")
    postgresql_sql.append("")
    
    for table_name in django_tables:
        postgresql_sql.append(f"-- Таблица: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        create_sql = f"CREATE TABLE {table_name} (\n"
        column_defs = []
        
        for col in columns:
            col_id, name, type_name, not_null, default_val, pk = col
            
            # Конвертируем типы данных для PostgreSQL
            pg_type = convert_sqlite_type_to_postgresql(type_name)
            
            col_def = f"    {name} {pg_type}"
            
            if not_null:
                col_def += " NOT NULL"
            if pk:
                col_def += " PRIMARY KEY"
            if default_val:
                pg_default = convert_default_value(default_val)
                col_def += f" DEFAULT {pg_default}"
                
            column_defs.append(col_def)
        
        create_sql += ",\n".join(column_defs)
        create_sql += "\n);"
        postgresql_sql.append(create_sql)
        postgresql_sql.append("")
    
    # Кастомные таблицы (используем схему из database_schema.sql)
    postgresql_sql.append("-- КАСТОМНЫЕ ТАБЛИЦЫ")
    postgresql_sql.append("-- ===========================================")
    postgresql_sql.append("")
    
    # Читаем схему из database_schema.sql
    schema_file = Path(__file__).parent / 'database_schema.sql'
    if schema_file.exists():
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        # Извлекаем CREATE TABLE для кастомных таблиц
        lines = schema_content.split('\n')
        in_custom_tables = False
        
        for line in lines:
            if '-- Таблица ролей пользователей' in line:
                in_custom_tables = True
            elif line.startswith('-- Создание индексов') or line.startswith('-- Вставка базовых данных'):
                in_custom_tables = False
            
            if in_custom_tables and line.strip():
                postgresql_sql.append(line)
        
        postgresql_sql.append("")
    
    # Индексы
    postgresql_sql.append("-- ИНДЕКСЫ")
    postgresql_sql.append("-- ===========================================")
    postgresql_sql.append("")
    
    cursor.execute("""
        SELECT name, sql FROM sqlite_master 
        WHERE type='index' AND sql IS NOT NULL
        ORDER BY name
    """)
    indexes = cursor.fetchall()
    
    for index_name, index_sql in indexes:
        if index_sql:
            # Конвертируем индексы для PostgreSQL
            pg_index_sql = convert_index_to_postgresql(index_sql)
            postgresql_sql.append(f"-- Индекс: {index_name}")
            postgresql_sql.append(pg_index_sql + ";")
            postgresql_sql.append("")
    
    # Последовательности для автоинкремента
    postgresql_sql.append("-- ПОСЛЕДОВАТЕЛЬНОСТИ")
    postgresql_sql.append("-- ===========================================")
    postgresql_sql.append("")
    
    for table in tables:
        table_name = table[0]
        postgresql_sql.append(f"CREATE SEQUENCE IF NOT EXISTS {table_name}_id_seq;")
        postgresql_sql.append(f"ALTER TABLE {table_name} ALTER COLUMN id SET DEFAULT nextval('{table_name}_id_seq');")
        postgresql_sql.append(f"ALTER SEQUENCE {table_name}_id_seq OWNED BY {table_name}.id;")
        postgresql_sql.append("")
    
    # Данные (опционально)
    postgresql_sql.append("-- БАЗОВЫЕ ДАННЫЕ")
    postgresql_sql.append("-- ===========================================")
    postgresql_sql.append("")
    
    # Добавляем базовые данные из database_schema.sql
    if schema_file.exists():
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        lines = schema_content.split('\n')
        in_data_section = False
        
        for line in lines:
            if '-- Вставка базовых данных' in line:
                in_data_section = True
            elif line.startswith('-- Создание индексов'):
                in_data_section = False
            
            if in_data_section and line.strip():
                postgresql_sql.append(line)
    
    conn.close()
    
    # Записываем в файл
    output_file = Path(__file__).parent / 'postgresql_complete_database.sql'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(postgresql_sql))
    
    print(f"✅ PostgreSQL файл создан: {output_file}")
    print(f"📊 Размер файла: {output_file.stat().st_size} байт")
    
    return output_file

def convert_sqlite_type_to_postgresql(sqlite_type):
    """Конвертирует типы данных SQLite в PostgreSQL"""
    type_mapping = {
        'INTEGER': 'INTEGER',
        'REAL': 'DOUBLE PRECISION',
        'TEXT': 'TEXT',
        'BLOB': 'BYTEA',
        'BOOLEAN': 'BOOLEAN',
        'DATETIME': 'TIMESTAMP',
        'DATE': 'DATE',
        'TIME': 'TIME',
        'DECIMAL': 'DECIMAL',
        'BIGINT': 'BIGINT',
        'VARCHAR': 'VARCHAR',
        'JSON': 'JSONB'
    }
    
    # Извлекаем базовый тип
    base_type = sqlite_type.upper().split('(')[0]
    return type_mapping.get(base_type, 'TEXT')

def convert_default_value(default_val):
    """Конвертирует значения по умолчанию"""
    if default_val == 'TRUE':
        return 'true'
    elif default_val == 'FALSE':
        return 'false'
    elif default_val == 'NULL':
        return 'NULL'
    elif default_val.startswith("'") and default_val.endswith("'"):
        return default_val
    else:
        return default_val

def convert_index_to_postgresql(index_sql):
    """Конвертирует индексы для PostgreSQL"""
    # Простая конвертация - можно расширить при необходимости
    return index_sql

if __name__ == "__main__":
    export_to_postgresql() 