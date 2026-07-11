from dotenv import load_dotenv
load_dotenv()

from mood.gemini_analyzer import GeminiAnalyzer
import json

a = GeminiAnalyzer()
print('Available:', a.is_available)

if not a.is_available:
    print('API Key not loaded into GeminiAnalyzer')
else:
    try:
        from google import genai
        from google.genai import types
        import os
        
        client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="سلام، فقط بگو OK",
        )
        print('Gemini response:', response.text)
        print('Gemini is working!')
        
    except Exception as e:
        print('Gemini ERROR:', type(e).__name__, str(e))