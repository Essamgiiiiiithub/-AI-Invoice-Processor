import os

# إنشاء المجلدات المطلوبة
folders = ['uploads', 'outputs', 'database']
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"Created: {folder}/")

# إنشاء ملفات المشروع الفارغة
files = [
    'ocr_engine.py',
    'ai_extractor.py', 
    'data_handler.py',
    'app.py'
]
for file in files:
    if not os.path.exists(file):
        open(file, 'w').close()
        print(f"Created: {file}")
    else:
        print(f"Already exists: {file}")

print("\nProject structure ready!")