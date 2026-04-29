import os
from google import genai

os.environ["GOOGLE_API_KEY"] = "AIzaSyAZCwz_75h5-fCFLOwhx2Z7M59PIDrLNLg"
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

print("--- ALL AVAILABLE MODELS ---")
try:
    for m in client.models.list():
        print(f"Model: {m}")
except Exception as e:
    print(f"Error: {e}")
