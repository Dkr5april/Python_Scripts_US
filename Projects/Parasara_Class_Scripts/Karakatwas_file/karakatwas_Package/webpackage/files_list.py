import os
import streamlit as st
import json

def load_data():
    # సర్వర్ లో ఏయే ఫైల్స్ ఉన్నాయో చూపిస్తుంది
    files_in_dir = os.listdir('.')
    st.write("సర్వర్ లో ఉన్న ఫైల్స్:", files_in_dir)
    
    filename = 'karakatwas.json'
    
    if filename in files_in_dir:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        st.error(f"ఎర్రర్: {filename} సర్వర్ లో కనిపించడం లేదు! ఫైల్స్ జాబితా పైన చూడండి.")
        return None