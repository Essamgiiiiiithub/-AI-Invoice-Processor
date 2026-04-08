import json
import os
from groq import Groq
from dotenv import load_dotenv
from cache_manager import get_cached, set_cache

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_document_data(text):
    """استخراج بيانات الوثيقة بالذكاء الاصطناعي"""

    # تحقق من التخزين المؤقت
    cached_result = get_cached(text, cache_type="extraction")
    if cached_result:
        print("استخدام النتيجة المحفوظة")
        return cached_result

    # تقصير النص إذا كان طويلاً
    max_chars = 3000
    if len(text) > max_chars:
        text = text[:max_chars]
        print(f"تم تقصير النص إلى {max_chars} حرف")

    prompt = f"""Extract document data. Return ONLY this JSON, no markdown:
{{
    "document_type": "invoice/receipt/contract/letter/etc or null",
    "supplier_name": "exact name or null",
    "invoice_number": "number or null",
    "date": "YYYY-MM-DD or null",
    "total_amount": "amount with currency or null",
    "numeric_total": 0.0,
    "tax_amount": "tax with currency or null",
    "numeric_tax": 0.0,
    "currency": "EGP/USD/SAR/etc or null",
    "items": ["item 1", "item 2"],
    "subtotal": "subtotal or null",
    "payment_method": "cash/card/transfer or null",
    "notes": "extra info or null",
    "title": "title or null",
    "description": "brief description or null"
}}

Document Text:
{text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise document parser. Output ONLY valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=800,
        )

        result = response.choices[0].message.content.strip()

        # تنظيف الرد
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])
        result = result.strip()

        data = json.loads(result)

        # استخراج الأرقام إذا لم تكن موجودة
        if not data.get("numeric_total") and data.get("total_amount"):
            import re
            nums = re.findall(r"[\d,]+\.?\d*", str(data["total_amount"]))
            if nums:
                data["numeric_total"] = float(nums[0].replace(",", ""))

        if not data.get("numeric_tax") and data.get("tax_amount"):
            import re
            nums = re.findall(r"[\d,]+\.?\d*", str(data["tax_amount"]))
            if nums:
                data["numeric_tax"] = float(nums[0].replace(",", ""))

        # حفظ في التخزين المؤقت
        set_cache(text, data, cache_type="extraction", ttl_hours=24)

        return data

    except json.JSONDecodeError as e:
        print(f"خطأ في تحليل JSON: {e}")
        return {"error": "Failed to parse AI response"}
    except Exception as e:
        print(f"خطأ في API: {e}")
        return {"error": str(e)}

