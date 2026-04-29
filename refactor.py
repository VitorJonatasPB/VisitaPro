import os
import re

# We will recursively walk through the directory and do content replacements
# And rename files and directories that contain 'empresa', 'contato', etc.

REPLACEMENTS = [
    ("Empresa", "Empresa"),
    ("empresa", "empresa"),
    ("EMPRESA", "EMPRESA"),
    ("Contato", "Contato"),
    ("contato", "contato"),
    ("CONTATO", "CONTATO"),
    ("Visitas Empresares", "Visitas Corporativas"),
    ("visitas_empresares", "visitas_corporativas"),
    ("Visitas_Empresares", "Visitas_Corporativas"),
    ("visitaspro", "visitaspro"),
    ("VisitasPro", "VisitasPro"),
    ("VISITASPRO", "VISITASPRO")
]

# We need to preserve 'visitas' so we don't mess up the core app names
# Exclusions
EXCLUDE_DIRS = ['.git', '.venv', 'node_modules', '__pycache__', 'staticfiles', '.expo']
EXCLUDE_EXTS = ['.sqlite3', '.pyc', '.png', '.jpg', '.jpeg', '.webp']

def process_file_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for old, new in REPLACEMENTS:
            new_content = new_content.replace(old, new)
            
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
    except Exception as e:
        print(f"Skipping content for {filepath}: {e}")

def process_path_names(root_dir):
    # Rename files first, then directories bottom-up
    for root, dirs, files in os.walk(root_dir, topdown=False):
        # Exclude
        if any(ex in root for ex in EXCLUDE_DIRS):
            continue
            
        # Files
        for f in files:
            if any(f.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
                
            old_path = os.path.join(root, f)
            new_f = f
            for old, new in REPLACEMENTS:
                new_f = new_f.replace(old, new)
            
            if f != new_f:
                new_path = os.path.join(root, new_f)
                os.rename(old_path, new_path)
                
        # Dirs
        for d in dirs:
            if d in EXCLUDE_DIRS:
                continue
                
            old_path = os.path.join(root, d)
            new_d = d
            for old, new in REPLACEMENTS:
                new_d = new_d.replace(old, new)
                
            if d != new_d:
                new_path = os.path.join(root, new_d)
                os.rename(old_path, new_path)

def process_all_contents(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if any(ex in root for ex in EXCLUDE_DIRS):
            continue
            
        for f in files:
            if any(f.endswith(ext) for ext in EXCLUDE_EXTS):
                continue
                
            filepath = os.path.join(root, f)
            process_file_content(filepath)

if __name__ == '__main__':
    base_dir = r"c:\Users\Vitor.Paiva\Documents\Programacao\Python\projetos\visitaspro - Copia"
    print("Processing contents...")
    process_all_contents(base_dir)
    print("Processing names...")
    process_path_names(base_dir)
    print("Done!")
