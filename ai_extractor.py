import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_invoice_data(text):
    """استخراج بيانات الفاتورة بالذكاء الاصطناعي"""

    prompt = f"""
Extract invoice data from the text below. Reply with ONLY a JSON object, no extra text:

{{
    "supplier_name": "company name or null",
    "invoice_number": "invoice number or null",
    "date": "date or null",
    "total_amount": "total amount or null",
    "tax_amount": "tax amount or null",
    "items": ["list of items or services"]
}}

Text:
{text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an invoice parser. Reply with valid JSON only. No markdown, no explanation."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    result = response.choices[0].message.content.strip()
    
    # تنظيف الرد لو فيه markdown
    if result.startswith("```"):
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]
    result = result.strip()

    data = json.loads(result)
    return data


# ── تجربة الكود ──
if __name__ == "__main__":
    test_text = """
    Array Training Center
    Invoice No: INV-2024-001
    Date: 15/7/2024
    Total: 5000 EGP
    Tax: 750 EGP
    Services: AI Diploma Course
    """

    print("🤖 AI Extractor Test")
    print("=" * 40)

    data = extract_invoice_data(test_text)

    print("\n📊 Extracted Data:")
    print(json.dumps(data, ensure_ascii=False, indent=2))