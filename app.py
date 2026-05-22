import streamlit as st
from PIL import Image
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Import our custom modules
from vlm_verifier import analyze_plate_with_vlm
from nutrition_api import get_nutrition_data

# 1. Set page config to 'wide' layout
st.set_page_config(page_title="PlateCheck AI", page_icon="🥗", layout="wide")

# 2. Initialize Persistent Historical Log in Session State if it doesn't exist yet
if "meal_history" not in st.session_state:
    st.session_state.meal_history = []

st.title("🥗 PlateCheck: Semantic AI Orchestrator")
st.caption("Using Advanced Vision-Language processing to visually isolate overlapping food segments.")
st.markdown("---")

# 3. Establish the Split-Screen Dashboard Columns
left_col, right_col = st.columns([1, 1.2], gap="large")

# --- LEFT COLUMN: CONTROL & INPUT PANEL ---
with left_col:
    st.subheader("📸 Input Interface")
    uploaded_file = st.file_uploader("Upload your meal photo...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Target Meal Layout", width=450)

# --- RIGHT COLUMN: DYNAMIC AI RUNTIME PANEL ---
with right_col:
    st.subheader("🎯 Real-Time Analysis Grid")
    
    if uploaded_file is not None:
        with st.spinner("Analyzing plate composition using semantic vision..."):
            detected_components = analyze_plate_with_vlm(image)
            
        total_calories = 0
        total_carbs = 0
        total_protein = 0
        total_fat = 0
        
        if detected_components is None:
            st.error("🚨 Configuration Error: Could not connect to the AI service. Please verify API key!")
        
        elif len(detected_components) == 0:
            st.warning("🔍 No food detected on the plate. Try uploading a clearer picture of your meal!")
        
        else:
            st.markdown("### 📋 Identified Items")
            item_names_list = []
            
            for item in detected_components:
                macros = get_nutrition_data(item.name)
                item_names_list.append(item.name.title())
                
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

            if total_calories > 0:
                st.markdown("---")
                st.markdown("### 📊 Combined Plate Nutritional Assessment")
                
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric("Calories", f"{int(total_calories)} kcal")
                m_col2.metric("Carbs", f"{round(total_carbs, 1)}g")
                m_col3.metric("Protein", f"{round(total_protein, 1)}g")
                m_col4.metric("Fat", f"{round(total_fat, 1)}g")
                
                labels = ['Carbohydrates', 'Protein', 'Fat']
                values = [total_carbs, total_protein, total_fat]
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, 
                                             marker=dict(colors=['#FF4B4B', '#004280', '#FFA500']))])
                fig.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=280)
                st.plotly_chart(fig, width="stretch")
                
                # 🚀 LOGGING MECHANISM: Check if this exact file analysis has already been logged
                # This unique key prevent Streamlit from creating duplicate rows upon page reruns
                current_file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                
                if "last_logged_file" not in st.session_state or st.session_state.last_logged_file != current_file_key:
                    st.session_state.last_logged_file = current_file_key
                    st.session_state.meal_history.append({
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Meal Overview": ", ".join(item_names_list),
                        "Calories (kcal)": int(total_calories),
                        "Carbs (g)": round(total_carbs, 1),
                        "Protein (g)": round(total_protein, 1),
                        "Fat (g)": round(total_fat, 1)
                    })
                
    else:
        st.info("💡 Awaiting intake file. Drop a meal picture in the input panel to see the live metrics grid.")

# --- LOWER FULL-WIDTH PANEL: HISTORICAL ANALYTICS LOG ---
st.markdown("---")
st.subheader("📈 Patient Intake Longitudinal History")

if st.session_state.meal_history:
    # Convert session state list to a clean Pandas DataFrame for analytical presentation
    history_df = pd.DataFrame(st.session_state.meal_history)
    
    # Render the data frame seamlessly across the width of the screen
    st.dataframe(history_df, width="stretch", hide_index=True)
    
    # Provide an immediate CSV Export button for health-tech data pipeline simulation
    csv_data = history_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Clinical Nutrition Record (CSV)",
        data=csv_data,
        file_name="platecheck_patient_history.csv",
        mime="text/csv"
    )
else:
    st.caption("No data logged in history yet. Upload your first meal image above to start tracking longitudinal stats.")