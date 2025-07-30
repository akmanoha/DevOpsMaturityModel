
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fuzzywuzzy import process
import os

# File paths
mapping_file = 'DevOps_Maturity_Mapping.xlsx'
response_file = 'DevOps_Maturity_Assessment_Demo_Response.xlsx'
recommendation_file = 'recommendations_v1.xlsx'

# Load files
base_path = os.path.dirname(os.path.abspath(__file__))
print("Files in dir:", os.listdir(base_path))
mapping_path = os.path.join(base_path, mapping_file)
response_path = os.path.join(base_path, response_file)
recommendation_path = os.path.join(base_path, recommendation_file)
mapping_df = pd.read_excel(mapping_path)
response_df = pd.read_excel(response_path)
recommendation_xls = pd.ExcelFile(recommendation_path)

# Fuzzy match function
def fuzzy_match(question, choices, threshold=85):
    match, score = process.extractOne(question, choices)
    return match if score >= threshold else None

# Build mapping of questions to sections
question_to_section = {}
for _, row in mapping_df.iterrows():
    q_text = row['Question']
    section = row['Section']
    match = fuzzy_match(q_text, response_df.columns)
    if match:
        question_to_section[match] = section

# Get latest entry for each email
latest_entries = response_df.sort_values('Completion time').drop_duplicates('Email', keep='last')
selected_email = st.selectbox("Select Email", latest_entries['Email'])
user_row = latest_entries[latest_entries['Email'] == selected_email].iloc[0]

# Calculate section scores
section_scores = {}
for question, section in question_to_section.items():
    value = user_row.get(question)
    if pd.notnull(value):
        try:
            score = int(str(value).split('.')[0])
            section_scores.setdefault(section, []).append(score)
        except:
            continue

average_scores = {section: round(np.mean(scores), 2) for section, scores in section_scores.items()}

# Display scores
st.subheader("DevOps Maturity Scores by Section")
score_df = pd.DataFrame(list(average_scores.items()), columns=["Section", "Score"])
st.dataframe(score_df)

# Charts
fig_bar = px.bar(score_df, x="Section", y="Score", color="Score", text="Score", title="Section-wise Maturity Scores")
st.plotly_chart(fig_bar)

fig_radar = px.line_polar(score_df, r="Score", theta="Section", line_close=True, title="Radar Chart - Section Scores")
st.plotly_chart(fig_radar)

# Recommendations section
st.subheader("Recommendations by Section")
for section, avg_score in average_scores.items():
    level = int(round(avg_score))
    if section in recommendation_xls.sheet_names:
        rec_df = pd.read_excel(recommendation_file, sheet_name=section)
        rec_df.columns = rec_df.columns.str.strip()
        rec_df['Maturity Levels'] = pd.to_numeric(rec_df['Maturity Levels'], errors='coerce')
        matched_rows = rec_df[rec_df['Maturity Levels'] == level][['Supporting Categories', 'Recommendations']].dropna()
        with st.expander(f"{section} - Level {level} Recommendations"):
            for _, row in matched_rows.iterrows():
                st.markdown(f"**Category**: {row['Supporting Categories']}")
                st.markdown(f"**Recommendation**: {row['Recommendations']}")
