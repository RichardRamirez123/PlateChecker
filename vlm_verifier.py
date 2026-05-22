import os
import random
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
# 1. Import the dotenv loader
from dotenv import load_dotenv
import json

# 2. Automatically load the variables from your hidden .env file
load_dotenv()

class FoodItem(BaseModel):
    name: str = Field(description="The clean name of the specific food item or side dish found on the plate.")
    estimated_weight_grams: int = Field(description="An estimated weight of this specific component in grams based on standard serving sizes.")

class PlateAnalysis(BaseModel):
    components: list[FoodItem]

def analyze_plate_with_vlm(pil_image):
    """Passes the image to Gemini 2.5 Flash to cleanly extract individual food sections."""
    
    # 1. Grab the keys from environment variables
    api_keys_raw = os.environ.get("GEMINI_API_KEYS")
    api_keys = []
    
    if api_keys_raw:
        # Check if it looks like a JSON list string (local .env issue)
        if isinstance(api_keys_raw, str) and api_keys_raw.strip().startswith("["):
            try:
                api_keys = json.loads(api_keys_raw)
            except Exception:
                pass
        # If it's already a clean parsed list (Streamlit Cloud behavior)
        elif isinstance(api_keys_raw, list):
            api_keys = api_keys_raw
        # If it's a comma-separated string
        elif isinstance(api_keys_raw, str):
            api_keys = [k.strip() for k in api_keys_raw.split(",") if k.strip()]

    # Fallback to single key if multiple-keys configuration isn't set up yet
    if not api_keys:
        single_key = os.environ.get("GEMINI_API_KEY")
        if single_key:
            api_keys = [single_key]

    if not api_keys:
        print("🚨 Error: No API keys found in system configurations!")
        return None

    # 2. Pick a random key from your clean pool
    chosen_key = random.choice(api_keys)
    
    # Optional debug print so you can see which key is active in the terminal
    print(f"🔑 Live Key Selected (Trimming for safety): ...{chosen_key[-6:]}")
    
    # 3. Initialize your Google GenAI client with the clean key
    client = genai.Client(api_key=chosen_key)
    
    prompt = """
    You are an advanced medical-grade nutritional AI. Look at the provided image of this meal layout. 
    Even if the food components are touching, mixed, or sitting on top of each other, use your 
    deep visual reasoning to isolate each distinct culinary ingredient, macro-group, or side dish.
    
    Break down the plate into its individual component sections (e.g., if you see salmon, broccoli, and rice, 
    extract them as three separate items). Estimate a realistic serving weight in grams for each.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[pil_image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PlateAnalysis,
                temperature=0.2 
            ),
        )
        return response.parsed.components
    except Exception as e:
        print(f"VLM Processing Error: {e}")
        return []
