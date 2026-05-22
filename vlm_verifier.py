import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
# 1. Import the dotenv loader
from dotenv import load_dotenv

# 2. Automatically load the variables from your hidden .env file
load_dotenv()

class FoodItem(BaseModel):
    name: str = Field(description="The clean name of the specific food item or side dish found on the plate.")
    estimated_weight_grams: int = Field(description="An estimated weight of this specific component in grams based on standard serving sizes.")

class PlateAnalysis(BaseModel):
    components: list[FoodItem]

def analyze_plate_with_vlm(pil_image):
    """Passes the image to Gemini 2.5 Flash to cleanly extract individual food sections."""
    # The client now seamlessly reads the key from your hidden .env file!
    client = genai.Client()
    
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