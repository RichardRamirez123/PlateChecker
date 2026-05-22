import streamlit as st
from PIL import Image
import plotly.graph_objects as go

# Import our custom modules
from vlm_verifier import analyze_plate_with_vlm
from nutrition_api import get_nutrition_data

# 1. Set page config to 'wide' layout so the side-by-side dashboard has breathing room
st.set_page_config(page_title="PlateCheck AI", page_icon="🥗", layout="wide")

st.title("🥗 PlateCheck: Semantic AI Orchestrator")
st.caption("Using Advanced Vision-Language processing to visually isolate overlapping food segments.")
st.markdown("---")

# 2. Establish the Split-Screen Dashboard Columns
left_col, right_col = st.columns([1, 1.2], gap="large")

# --- LEFT COLUMN: CONTROL & INPUT PANEL ---
with left_col:
    st.subheader("📸 Input Interface")
    uploaded_file = st.file_uploader("Upload your meal photo...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        # Use width rather than deprecated container parameters to keep terminal console warnings clean
        st.image(image, caption="Target Meal Layout", width=450)

# --- RIGHT COLUMN: DYNAMIC AI RUNTIME PANEL ---
with right_col:
    st.subheader("🎯 Real-Time Analysis Grid")
    
    # Only execute tracking calculations if a file has actually been uploaded
    if uploaded_file is not None:
        with st.spinner("Analyzing plate composition using semantic vision..."):
            detected_components = analyze_plate_with_vlm(image)
            
        total_calories = 0
        total_carbs = 0
        total_protein = 0
        total_fat = 0
        
        # Structure Check A: Check if API environment/configuration failed
        if detected_components is None:
            st.error("🚨 Configuration Error: Could not connect to the AI service. Please verify API key!")
        
        # Structure Check B: Check if plate returned successfully but was read as empty
        elif len(detected_components) == 0:
            st.warning("🔍 No food detected on the plate. Try uploading a clearer picture of your meal!")
        
        # Structure Check C: Success path processing logic
        else:
            st.markdown("### 📋 Identified Items")
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
                
                st.markdown(f"**✅ {item.name.title()}** (~{item.estimated_weight_grams}g)")
                st.caption(f"↳ *Calculated:* {int(item_cals)} kcal | Carbs: {round(item_carbs, 1)}g | Protein: {round(item_protein, 1)}g")

            # Only render macro dashboards if valid food items actually drove calculation totals up
            if total_calories > 0:
                st.markdown("---")
                st.markdown("### 📊 Combined Plate Nutritional Assessment")
                
                # Display high-level metrics across 4 parallel small columns
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric("Calories", f"{int(total_calories)} kcal")
                m_col2.metric("Carbs", f"{round(total_carbs, 1)}g")
                m_col3.metric("Protein", f"{round(total_protein, 1)}g")
                m_col4.metric("Fat", f"{round(total_fat, 1)}g")
                
                # Build interactive central distribution donut chart
                labels = ['Carbohydrates', 'Protein', 'Fat']
                values = [total_carbs, total_protein, total_fat]
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, 
                                             marker=dict(colors=['#FF4B4B', '#004280', '#FFA500']))])
                fig.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=280)
                st.plotly_chart(fig, width="stretch")
                
    else:
        # Prompt user to interact when dashboard boots up completely empty
        st.info("💡 Awaiting intake file. Drop a meal picture in the input panel to see the live metrics grid.")