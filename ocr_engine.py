import os
import shutil
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# مسار Tesseract
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
        print(f"⚠️ POPPLER_PATH is set but invalid: {candidate}")

    # قائمة مسارات Poppler الافتراضية
    DEFAULT_POPPLER_PATHS = [
        r"C:\Users\hp\Downloads\poppler\Library\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\Program Files (x86)\poppler\bin",
        # أضف مسارات أخرى إذا لزم الأمر
    ]

    for path in DEFAULT_POPPLER_PATHS:
        if _is_valid_poppler_path(path):
            return path

    return None


def read_image(image_path):
    """قراءة نص من صورة"""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='ara+eng')
        return text.strip(), None
    except Exception as e:
        return None, f"Image OCR error: {e}"


def read_pdf(pdf_path):
    """قراءة نص من PDF بتحويل الصفحات إلى صور"""
    poppler_path = _get_poppler_path()
    try:
        if poppler_path:
            images = convert_from_path(pdf_path, poppler_path=poppler_path)
        else:
            images = convert_from_path(pdf_path)

        full_text = ""
        for img in images:
            text = pytesseract.image_to_string(img, lang='ara+eng')
            full_text += text + "\n"
        return full_text.strip(), None
    except Exception as e:
        print(f"❌ PDF conversion error: {e}")
        if poppler_path is None:
            message = (
                "Unable to process PDF. Poppler was not found. "
                "Install Poppler and set POPPLER_PATH to the bin directory, or add Poppler binaries to PATH. "
                "See https://pdf2image.readthedocs.io/en/latest/installation.html. "
                f"Current POPPLER_PATH={poppler_path!r}. Error: {e}"
            )
        else:
            message = (
                "Unable to process PDF. The configured POPPLER_PATH appears invalid or missing required binaries. "
                "Ensure pdfinfo.exe and pdftoppm.exe are present in the directory. "
                f"POPPLER_PATH={poppler_path!r}. Error: {e}"
            )
        return None, message


def extract_text(file_path):
    """الدالة الرئيسية"""
    ext = os.path.splitext(file_path)[1].lower()
    print(f"📂 Processing: {file_path}")

    if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        text, error = read_image(file_path)
    elif ext == '.pdf':
        text, error = read_pdf(file_path)
    else:
        return None, "❌ Unsupported file type"

    if text:
        print("✅ Text extracted!")
        return text, None
    if error:
        return None, error
    return None, "❌ No text found"

# ── تجربة الكود ──
if __name__ == "__main__":
    print("🔍 OCR Engine Test")
    print("=" * 40)

    # تجربة على شهادتك من Array!
    test_file = "uploads/test_invoice.jpg.jpeg"

    if os.path.exists(test_file):
        text, error = extract_text(test_file)
        if text:
            print("\n📝 Extracted Text:")
            print(text)
        else:
            print(error)
    else:
        print("⚠️  ضع صورة في مجلد uploads باسم test_invoice.jpg")