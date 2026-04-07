import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_document_data(text):
    """استخراج بيانات الوثيقة بالذكاء الاصطناعي - نسخة محسّنة"""

    prompt = f"""
You are an expert document data extraction system. Analyze the document text carefully and extract ALL relevant information with maximum accuracy.

RULES:
- Extract EVERY piece of information you can find (names, dates, amounts, descriptions, etc.)
- For amounts: include the currency symbol/code (EGP, USD, SAR, etc.) if present
- For dates: standardize to YYYY-MM-DD format if possible
- For items/lists: list each item separately
- If a field is truly missing, use null — never guess
- total_amount should be any final total amount if present
- Extract numeric_total as a plain number (no currency) for calculations if applicable
- Identify the document type if possible (invoice, receipt, contract, letter, etc.)

Return ONLY this JSON object, no markdown, no explanation:

{{
    "document_type": "invoice/receipt/contract/letter/etc or null",
    "supplier_name": "exact company/person name or null",
    "invoice_number": "invoice/receipt number or null",
    "date": "date string or null",
    "total_amount": "amount with currency e.g. 5000 EGP or null",
    "numeric_total": 5000.0,
    "tax_amount": "tax with currency or null",
    "numeric_tax": 750.0,
    "currency": "EGP/USD/SAR/etc or null",
    "items": ["item 1", "item 2"],
    "subtotal": "subtotal before tax or null",
    "payment_method": "cash/card/transfer or null",
    "notes": "any extra info or null",
    "title": "document title or subject or null",
    "description": "brief description of the document content or null"
}}

Document Text:
{text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise document parser. "
                    "Output ONLY valid JSON. No markdown fences, no preamble, no explanation. "
                    "Be thorough — extract every piece of information present in the text."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=1024,
    )

    result = response.choices[0].message.content.strip()

    # تنظيف الرد لو فيه markdown
    if result.startswith("```"):
        lines = result.split("\n")
        result = "\n".join(lines[1:-1])
    result = result.strip()

    data = json.loads(result)

    # Fallback: استخرج الرقم من total_amount لو numeric_total مش موجود
    if not data.get("numeric_total") and data.get("total_amount"):
        import re
        nums = re.findall(r"[\d,]+\.?\d*", str(data["total_amount"]))
        if nums:
            data["numeric_total"] = float(nums[0].replace(",", ""))

    return data


# ── تجربة الكود ──
if __name__ == "__main__":
    test_text = """
    Array Training Center
    Invoice No: INV-2024-001
    Date: 15/7/2024
    Subtotal: 4,250 EGP
    Tax (15%): 750 EGP
    Total: 5,000 EGP
    Payment: Bank Transfer
    Services: AI Diploma Course, Python Bootcamp
    """

    print("🤖 AI Extractor Test (Enhanced)")
    print("=" * 40)
    data = extract_document_data(test_text)
    print("\n📊 Extracted Data:")
    print(json.dumps(data, ensure_ascii=False, indent=2))
