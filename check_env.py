
import sys
try:
    import streamlit
    print("Streamlit: OK")
except ImportError as e:
    print(f"Streamlit: Fail ({e})")

try:
    import google.generativeai as genai
    print("Google Generative AI: OK")
except ImportError as e:
    print(f"Google Generative AI: Fail ({e})")

try:
    from pptx import Presentation
    print("python-pptx: OK")
except ImportError as e:
    print(f"python-pptx: Fail ({e})")
