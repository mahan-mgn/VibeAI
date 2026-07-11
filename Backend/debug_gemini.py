from dotenv import load_dotenv
load_dotenv()

import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# متن بدون نیم‌فاصله
text = "امروز خیلی خسته ام"

prompt = text + "\n\n"
prompt += "زمان فعلی: morning\n\n"
prompt += "بر اساس متن بالا، احساس کاربر را تحلیل کن و فقط یک JSON برگردان.\n"
prompt += "mood باید یکی از این ها باشه: tired, stressed, happy, excited, calm, anxious, sad, bored, neutral\n"
prompt += "energy باید یکی از این ها باشه: low, medium, high\n"
prompt += "activity باید یکی از این ها باشه: coding, studying, resting, exercise, general\n\n"
prompt += "نمونه خروجی:\n"
prompt += '{"mood": "tired", "moods": {"tired": 8}, "energy": "low", "activity": "general", "time_period": "night", "confidence": 0.9, "negations_detected": []}'

print("PROMPT (repr):")
print(repr(prompt))
print()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=400,
        response_mime_type="application/json",
    ),
)

print("RESPONSE:")
print(repr(response.text))

from mood.gemini_analyzer import GeminiAnalyzer
import json

a = GeminiAnalyzer()
result = a.analyze("امروز خیلی خسته‌ام")
print("\nنتیجه نهایی:")
print(json.dumps(result, ensure_ascii=False, indent=2) if result else "NONE")