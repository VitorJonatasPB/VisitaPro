# -*- coding: utf-8 -*-
"""
Script para verificar quais tabelas do Django estao faltando no banco
e cria-las sem apagar os dados existentes.

Execute com:
    python fix_missing_tables.py
dentro da pasta backend/
"""
import os
import sys
import django

# Configura o ambiente Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visitaPro.settings')

# Carrega .env manualmente antes do setup
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

django.setup()

from django.db import connection
from django.apps import apps

def get_existing_tables():
    """Retorna o conjunto de tabelas que existem no banco."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        return {row[0] for row in cursor.fetchall()}

def get_django_tables():
    """Retorna todas as tabelas que o Django espera que existam."""
    tables = {}
    for model in apps.get_models():
        table_name = model._meta.db_table
        tables[table_name] = model
    return tables

def create_missing_tables():
    existing = get_existing_tables()
    django_tables = get_django_tables()

    print("=" * 60)
    print("TABELAS EXISTENTES NO BANCO:")
    for t in sorted(existing):
        print(f"  [OK] {t}")

    missing = {t: m for t, m in django_tables.items() if t not in existing}

    print("\n" + "=" * 60)
    if not missing:
        print("[OK] Nenhuma tabela faltando! O banco esta em sincronia.")
        return

    print(f"TABELAS FALTANDO ({len(missing)}):")
    for t in sorted(missing.keys()):
        print(f"  [FALTA] {t}")

    print("\n" + "=" * 60)
    print("CRIANDO TABELAS FALTANTES...")

    with connection.schema_editor() as schema_editor:
        for table_name, model in missing.items():
            try:
                schema_editor.create_model(model)
                print(f"  [CRIADA] {table_name}")
            except Exception as e:
                print(f"  [ERRO] ao criar {table_name}: {e}")

    # Verifica M2M (tabelas intermediarias)
    print("\nVerificando tabelas M2M...")
    existing_after = get_existing_tables()
    for model in apps.get_models():
        for field in model._meta.many_to_many:
            m2m_table = field.remote_field.through._meta.db_table
            if m2m_table not in existing_after and not field.remote_field.through._meta.auto_created is False:
                try:
                    with connection.schema_editor() as schema_editor:
                        schema_editor.create_model(field.remote_field.through)
                    print(f"  [CRIADA M2M] {m2m_table}")
                except Exception as e:
                    if 'already exists' not in str(e):
                        print(f"  [ERRO M2M] {m2m_table}: {e}")

    print("\n[CONCLUIDO] Tabelas criadas com sucesso.")

if __name__ == '__main__':
    create_missing_tables()
