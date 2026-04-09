import os
import shutil
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from io import BytesIO
import fitz  # PyMuPDF - لا يحتاج Poppler

DEFAULT_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

def _find_tesseract():
    explicit = os.getenv("TESSERACT_CMD")
    if explicit and os.path.exists(explicit):
        return explicit

    for path in DEFAULT_TESSERACT_PATHS:
        if os.path.exists(path):
            return path

    found = shutil.which("tesseract")
    if found:
        return found

    return None

TESSERACT_CMD = _find_tesseract()
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
else:
    pytesseract.pytesseract.tesseract_cmd = "tesseract"

def _optimize_image(image, quality=85, max_width=2000):
    """تحسين الصورة لتسريع OCR"""
    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

    if image.mode in ('RGBA', 'LA', 'P'):
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = rgb_image

    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=quality, optimize=True)
    buffer.seek(0)
    return Image.open(buffer)

def _is_valid_poppler_path(path):
    if not path or not os.path.isdir(path):
        return False

    required_bins = ["pdfinfo.exe", "pdftoppm.exe"]
    return all(os.path.exists(os.path.join(path, binary)) for binary in required_bins)

def _get_poppler_path():
    candidate = os.getenv("POPPLER_PATH")
    if candidate:
        if _is_valid_poppler_path(candidate):
            return candidate
        print(f"مسار Poppler غير صحيح: {candidate}")

    DEFAULT_POPPLER_PATHS = [
        r"C:\Users\hp\Downloads\poppler\Library\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\Program Files (x86)\poppler\bin",
    ]

    for path in DEFAULT_POPPLER_PATHS:
        if _is_valid_poppler_path(path):
            return path

    return None

def read_image(image_path):
    """قراءة نص من صورة"""
    try:
        img = Image.open(image_path)
        img = _optimize_image(img, quality=80)
        text = pytesseract.image_to_string(img, lang='ara+eng')
        return text.strip(), None
    except Exception as e:
        return None, f"خطأ في قراءة الصورة: {e}"

def read_pdf(pdf_path):
    """قراءة نص من PDF"""
    try:
        # محاولة باستخدام PyMuPDF أولاً (لا يحتاج Poppler)
        pdf_document = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            # استخراج النص مباشرة من صفحة PDF
            text = page.get_text()
            full_text += text + "\n"
            
            # إذا لم نجد نصاً (صورة في PDF)، حول الصفحة إلى صورة وابحث عن النص
            if not text.strip():
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                img_data = pix.tobytes("ppm")
                img = Image.open(BytesIO(img_data))
                img = _optimize_image(img, quality=75)
                ocr_text = pytesseract.image_to_string(img, lang='ara+eng')
                full_text += ocr_text + "\n"
        
        pdf_document.close()
        return full_text.strip() if full_text.strip() else None, None
        
    except Exception as e:
        print(f"خطأ في قراءة PDF باستخدام PyMuPDF: {e}")
        
        # إذا فشل PyMuPDF، جرب pdf2image مع Poppler
        try:
            poppler_path = _get_poppler_path()
            if poppler_path:
                images = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=150)
            else:
                images = convert_from_path(pdf_path, dpi=150)

            full_text = ""
            for idx, img in enumerate(images):
                img = _optimize_image(img, quality=75)
                text = pytesseract.image_to_string(img, lang='ara+eng')
                full_text += text + "\n"
                del img

            return full_text.strip(), None
        except Exception as e2:
            print(f"خطأ في تحويل PDF: {e2}")
            message = (
                "لا يمكن معالجة PDF. حاول تثبيت PyMuPDF: pip install pymupdf\n"
                "أو ثبت Poppler وعيّن POPPLER_PATH بشكل صحيح.\n"
                f"الخطأ: {e2}"
            )
            return None, message

def extract_text(file_path):
    """استخراج النص من الملف"""
    ext = os.path.splitext(file_path)[1].lower()
    print(f"معالجة: {file_path}")

    if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        text, error = read_image(file_path)
    elif ext == '.pdf':
        text, error = read_pdf(file_path)
    else:
        return None, "نوع ملف غير مدعوم"

    if text:
        print("تم استخراج النص بنجاح")
        return text, None
    if error:
        return None, error
    return None, "لم يتم العثور على نص"