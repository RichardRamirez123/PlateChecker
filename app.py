import streamlit as st
from PIL import Image
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Import our custom modules
from vlm_verifier import analyze_plate_with_vlm
from nutrition_api import get_nutrition_data

# 1. Set page config to 'wide' layout (removed emoji)
st.set_page_config(page_title="PlateCheck AI", page_icon="🥗", layout="wide")

# 2. Initialize Persistent Historical Log in Session State if it doesn't exist yet
if "meal_history" not in st.session_state:
    st.session_state.meal_history = []

st.title("PlateCheck: Count Your Macros With A Snap")
st.caption("Advanced multi-object vision logic to instantly isolate and scan overlapping food items.")
st.markdown("---")

# 3. Establish the Split-Screen Dashboard Columns
left_col, right_col = st.columns([1, 1.2], gap="large")

# --- LEFT COLUMN: CONTROL & INPUT PANEL ---
with left_col:
    st.subheader("Show Me Your Plate")
    st.caption("Choose an intake channel to initialize the scan framework:")
    
    # Initialize persistent layout trackers in Session State
    if "input_source" not in st.session_state:
        st.session_state.input_source = None  # Tracks 'upload' or 'camera'
        
    # Render side-by-side action buttons
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.button("Upload Image", use_container_width=True):
            st.session_state.input_source = "upload"
            st.rerun()
            
    with btn_col2:
        if st.button("Open Camera", use_container_width=True, type="primary"):
            st.session_state.input_source = "camera"
            st.rerun()
            
    st.markdown("---")
    
    # Initialize our file buffer variable globally inside this execution frame
    uploaded_file = None
    
    # Dynamic input rendering paths
    if st.session_state.input_source == "upload":
        uploaded_file = st.file_uploader("Drop your meal image here...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # Create a clean local visual image frame preview container
            st.image(uploaded_file, caption="Target Lineup", width=450)
            
    elif st.session_state.input_source == "camera":
        if st.button("Kill Camera Feed", type="secondary"):
            st.session_state.input_source = None
            st.rerun()
        else:
            uploaded_file = st.camera_input("Line up your plate and capture")
            
    else:
        st.info("Select an active input stream above to begin your visual breakdown.")

# --- RIGHT COLUMN: DYNAMIC AI RUNTIME PANEL ---
with right_col:
    st.subheader("Nutrient Breakdown")
    
    if uploaded_file is not None:
        # Safely convert the raw file buffer into an image object here
        image = Image.open(uploaded_file)
        
        with st.spinner("Deconstructing plate architecture..."):
            detected_components = analyze_plate_with_vlm(image)
            
        total_calories = 0
        total_carbs = 0
        total_protein = 0
        total_fat = 0
        
        if detected_components is None:
            st.error("Connection failed. Check your network routing or API configuration keys.")
        
        elif len(detected_components) == 0:
            st.warning("Zero objects isolated. Try framing the food items in clearer lighting.")
        
        else:
            st.markdown("### Detected Lineup")
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
                
                st.markdown(f"**{item.name.title()}** (~{item.estimated_weight_grams}g)")
                st.caption(f"Yield: {int(item_cals)} kcal | Carbs: {round(item_carbs, 1)}g | Protein: {round(item_protein, 1)}g")

            if total_calories > 0:
                st.markdown("---")
                st.markdown("### Session Summary")
                
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric("Calories", f"{int(total_calories)} kcal")
                m_col2.metric("Carbs", f"{round(total_carbs, 1)}g")
                m_col3.metric("Protein", f"{round(total_protein, 1)}g")
                m_col4.metric("Fat", f"{round(total_fat, 1)}g")
                
                labels = ['Carbs', 'Protein', 'Fat']
                values = [total_carbs, total_protein, total_fat]
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, 
                                             marker=dict(colors=['#FF4B4B', '#004280', '#FFA500']))])
                fig.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=280)
                st.plotly_chart(fig, width="stretch")
                
                # LOGGING MECHANISM: Check if this exact file analysis has already been logged
                current_file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                
                if "last_logged_file" not in st.session_state or st.session_state.last_logged_file != current_file_key:
                    st.session_state.last_logged_file = current_file_key
                    st.session_state.meal_history.append({
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Meal Lineup": ", ".join(item_names_list),
                        "Calories (kcal)": int(total_calories),
                        "Carbs (g)": round(total_carbs, 1),
                        "Protein (g)": round(total_protein, 1),
                        "Fat (g)": round(total_fat, 1)
                    })
                
    else:
        st.info("Drop a meal snap on the left desk to populate your metrics layout.")

# --- LOWER FULL-WIDTH PANEL: HISTORICAL ANALYTICS LOG ---
st.markdown("---")
st.subheader("Plate Summary")

if st.session_state.meal_history:
    # Convert session state list to a clean Pandas DataFrame for analytical presentation
    history_df = pd.DataFrame(st.session_state.meal_history)
    
    # Render the data frame seamlessly across the width of the screen
    st.dataframe(history_df, width="stretch", hide_index=True)
    
    # Provide an immediate CSV Export button
    csv_data = history_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Dataset (CSV)",
        data=csv_data,
        file_name="platecheck_macro_vault.csv",
        mime="text/csv"
    )
else:
    st.caption("No capture sessions logged. Scan your first plate layout to populate historical analytics tracking.")