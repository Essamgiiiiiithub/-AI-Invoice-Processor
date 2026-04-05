import pytesseract
from PIL import Image
import os

# مسار Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def read_image(image_path):
    """قراءة نص من صورة"""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang='ara+eng')
    return text.strip()

def extract_text(file_path):
    """الدالة الرئيسية"""
    ext = os.path.splitext(file_path)[1].lower()
    print(f"📂 Processing: {file_path}")

    if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        text = read_image(file_path)
    else:
        return None, "❌ Unsupported file type"

    if text:
        print("✅ Text extracted!")
        return text, None
    else:
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