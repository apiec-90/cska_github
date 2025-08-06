#!/usr/bin/env python
import os
import sys
import django
import sqlite3
from pathlib import Path

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cska_django_supabase.settings')
django.setup()

def export_with_data():
    """
    Экспортирует БД с данными в PostgreSQL формат
    """
    print("🗄️ Экспорт БД с данными в PostgreSQL формат...")
    
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
    postgresql_sql.append("-- ПОЛНАЯ БАЗА ДАННЫХ CSKA ДЛЯ POSTGRESQL")
    postgresql_sql.append("-- Включает схему и данные")
    postgresql_sql.append("-- ===========================================")
    postgresql_sql.append("")
    
    # Сначала создаем таблицы (используем готовую схему)
    schema_file = Path(__file__).parent / 'postgresql_complete_database.sql'
    if schema_file.exists():
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_content = f.read()
        
        # Добавляем только CREATE TABLE
        lines = schema_content.split('\n')
        in_create_section = False
        
        for line in lines:
            if '-- DJANGO ТАБЛИЦЫ' in line:
                in_create_section = True
            elif '-- ИНДЕКСЫ' in line:
                in_create_section = False
            
            if in_create_section and line.strip():
                postgresql_sql.append(line)
    
    postgresql_sql.append("")
    postgresql_sql.append("-- ДАННЫЕ")
    postgresql_sql.append("-- ===========================================")
    postgresql_sql.append("")
    
    # Экспортируем данные из каждой таблицы
    for table in tables:
        table_name = table[0]
        
        # Получаем данные
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if rows:
            # Получаем названия колонок
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            postgresql_sql.append(f"-- Данные таблицы: {table_name}")
            postgresql_sql.append(f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES")
            
            # Формируем INSERT запросы
            insert_values = []
            for row in rows:
                formatted_values = []
                for value in row:
                    if value is None:
                        formatted_values.append('NULL')
                    elif isinstance(value, str):
                        # Экранируем кавычки
                        escaped_value = value.replace("'", "''")
                        formatted_values.append(f"'{escaped_value}'")
                    elif isinstance(value, bool):
                        formatted_values.append('true' if value else 'false')
                    else:
                        formatted_values.append(str(value))
                
                insert_values.append(f"({', '.join(formatted_values)})")
            
            # Добавляем INSERT запросы
            for i, value in enumerate(insert_values):
                if i == 0:
                    postgresql_sql.append(f"    {value},")
                elif i == len(insert_values) - 1:
                    postgresql_sql.append(f"    {value};")
                else:
                    postgresql_sql.append(f"    {value},")
            
            postgresql_sql.append("")
    
    conn.close()
    
    # Записываем в файл
    output_file = Path(__file__).parent / 'postgresql_with_data.sql'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(postgresql_sql))
    
    print(f"✅ PostgreSQL файл с данными создан: {output_file}")
    print(f"📊 Размер файла: {output_file.stat().st_size} байт")
    
    return output_file

if __name__ == "__main__":
    export_with_data() 