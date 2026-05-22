import streamlit as st
from PIL import Image
import plotly.graph_objects as go

# Import our custom modules
from vlm_verifier import analyze_plate_with_vlm
from nutrition_api import get_nutrition_data

st.set_page_config(page_title="PlateCheck AI", page_icon="🥗", layout="centered")
st.title("🥗 PlateCheck: Semantic AI Orchestrator")
st.write("Using Advanced Vision-Language processing to visually isolate overlapping food segments.")

uploaded_file = st.file_uploader("Upload your meal photo...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Target Meal Layout", width="stretch")
    
    with st.spinner("Analyzing plate composition using semantic vision..."):
        detected_components = analyze_plate_with_vlm(image)
        
    st.subheader("🎯 Identified Food Segments")
    
    total_calories = 0
    total_carbs = 0
    total_protein = 0
    total_fat = 0
    
    # Ensure the VLM actually returned a list (if it's None, the API call completely failed)
    if detected_components is None:
        st.error("Configuration Error: Could not connect to the AI service. Please verify API key!")
    
    # The API worked perfectly, but no food items were found in the image
    elif len(detected_components) == 0:
        st.warning("No food detected on the plate. Try uploading a clearer picture of your meal!")

    # Food was detected! Run the nutrition math and build the charts
    else:
        for item in detected_components:
            macros = get_nutrition_data(item.name)
            
            # Scale macros based on estimated weight (assuming database defaults to 100g base)
            scale = item.estimated_weight_grams / 100.0
            item_cals = macros['Calories'] * scale
            item_carbs = macros['Carbs'] * scale
            item_protein = macros['Protein'] * scale
            item_fat = macros['Fat'] * scale
            
            total_calories += item_cals
            total_carbs += item_carbs
            total_protein += item_protein
            total_fat += item_fat
            
            st.write(f"✅ **{item.name.title()}** (~{item.estimated_weight_grams}g)")
            st.caption(f"↳ *Estimated Contributions:* {int(item_cals)} kcal | Carbs: {round(item_carbs, 1)}g | Protein: {round(item_protein, 1)}g")

    # if detected_components:
    #     for item in detected_components:
    #         macros = get_nutrition_data(item.name)
            
    #         # Scale macros based on estimated weight (assuming database defaults to 100g base)
    #         scale = item.estimated_weight_grams / 100.0
    #         item_cals = macros['Calories'] * scale
    #         item_carbs = macros['Carbs'] * scale
    #         item_protein = macros['Protein'] * scale
    #         item_fat = macros['Fat'] * scale
            
    #         total_calories += item_cals
    #         total_carbs += item_carbs
    #         total_protein += item_protein
    #         total_fat += item_fat
            
    #         st.write(f"✅ **{item.name.title()}** (~{item.estimated_weight_grams}g)")
    #         st.caption(f"↳ *Estimated Contributions:* {int(item_cals)} kcal | Carbs: {round(item_carbs, 1)}g | Protein: {round(item_protein, 1)}g")
    # else:
    #     st.error("Could not complete analysis. Check that your terminal environment variable GEMINI_API_KEY is active!")

    if total_calories > 0:
        st.markdown("---")
        st.subheader("📊 Combined Plate Nutritional Assessment")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Grand Calories", f"{int(total_calories)} kcal")
        col2.metric("Grand Carbs", f"{round(total_carbs, 1)}g")
        col3.metric("Grand Protein", f"{round(total_protein, 1)}g")
        col4.metric("Grand Fat", f"{round(total_fat, 1)}g")
        
        labels = ['Carbohydrates', 'Protein', 'Fat']
        values = [total_carbs, total_protein, total_fat]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, 
                                     marker=dict(colors=['#FF4B4B', '#004280', '#FFA500']))])
        fig.update_layout(margin=dict(t=20, b=0, l=0, r=0))
        st.plotly_chart(fig)