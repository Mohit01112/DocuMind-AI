import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

print("--- Available Models ---")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(model.name)