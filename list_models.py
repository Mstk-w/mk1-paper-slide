import google.generativeai as genai
import sys

api_key = sys.argv[1]
genai.configure(api_key=api_key)

print("Available Models:")
for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)
