import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Check API key
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("❌ GOOGLE_API_KEY not found in .env file!")
    exit(1)

print(f"✓ API Key found: {api_key[:20]}...")

try:
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Create model (using Gemini 2.5 Flash - fast and capable!)
    model = genai.GenerativeModel('models/gemini-2.5-pro')
    
    # Test connection
    response = model.generate_content("Say 'Gemini connected successfully!' in one sentence.")
    
    print(f"\n{response.text}")
    print("\n✅ Gemini API is working!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")