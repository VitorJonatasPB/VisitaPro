"""
Reset completo do banco de dados PostgreSQL.
Apaga TODAS as tabelas e recria do zero via migrate.

Execute com:
    python reset_db.py
dentro da pasta backend/
"""
import os
import sys
import django
from pathlib import Path
from dotenv import load_dotenv

# Configura ambiente Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visitas_corporativas.settings')
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

django.setup()

from django.db import connection

def drop_all_tables():
    print("=" * 60)
    print("RESET COMPLETO DO BANCO DE DADOS")
    print("=" * 60)

    with connection.cursor() as cursor:
        # Lista todas as tabelas do schema public
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        tables = [row[0] for row in cursor.fetchall()]

    if not tables:
        print("[INFO] Banco ja esta vazio.")
        return

    print(f"\nApagando {len(tables)} tabela(s):")
    for t in tables:
        print(f"  - {t}")

    with connection.cursor() as cursor:
        # DROP com CASCADE resolve dependencias automaticamente
        for table in tables:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
            print(f"  [REMOVIDA] {table}")

    print("\n[OK] Todas as tabelas foram removidas.")

if __name__ == '__main__':
    drop_all_tables()
