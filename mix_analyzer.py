# mix_analyzer.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import xlsxwriter

st.set_page_config(page_title="Bitumen Mix Analyzer", layout="centered")
st.title("🛣️ Bitumen Mix Analyzer")
st.markdown("Upload your Excel file with mix data to analyze volumetric properties.")

uploaded_file = st.file_uploader("Upload Excel File", type=[".xlsx"])

def calculate_properties(df, Gb, Gsb):
    df['Va (%)'] = ((df['Gmm'] - df['Gmb']) / df['Gmm']) * 100
    df['VMA (%)'] = ((1 - df['Gmb'] / Gsb) * 100)
    df['VFB (%)'] = ((df['VMA (%)'] - df['Va (%)']) / df['VMA (%)']) * 100
    return df

def evaluate_specs(df):
    df['Va Status'] = df['Va (%)'].apply(lambda x: '✔️' if 3 <= x <= 5 else '❌')
    df['VMA Status'] = df['VMA (%)'].apply(lambda x: '✔️' if x >= 14 else '❌')
    df['VFB Status'] = df['VFB (%)'].apply(lambda x: '✔️' if 65 <= x <= 75 else '❌')
    return df

def generate_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
    output.seek(0)
    return output.read()

def download_link(data, filename, text):
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{text}</a>'
    return href

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Step 1: Enter Constants")
    Gb = st.number_input("Specific Gravity of Binder (Gb)", value=1.03, step=0.01)
    Gsb = st.number_input("Bulk Specific Gravity of Aggregate (Gsb)", value=2.6, step=0.01)

    if st.button("Analyze Mix"):
        df = calculate_properties(df, Gb, Gsb)
        df = evaluate_specs(df)

        st.subheader("Computed Volumetric Properties")
        st.dataframe(df.style.background_gradient(cmap='coolwarm', subset=['Va (%)', 'VMA (%)', 'VFB (%)']))

        # Sort by Bitumen Content before plotting
        df = df.sort_values(by='Bitumen Content (%)')

        fig1, ax1 = plt.subplots()
        ax1.plot(df['Bitumen Content (%)'], df['Va (%)'], marker='o', color='blue')
        ax1.set_title("Air Voids vs. Bitumen Content")
        ax1.set_xlabel("Bitumen Content (%)")
        ax1.set_ylabel("Air Voids (%)")
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots()
        ax2.plot(df['Bitumen Content (%)'], df['VMA (%)'], marker='s', color='green')
        ax2.set_title("VMA vs. Bitumen Content")
        ax2.set_xlabel("Bitumen Content (%)")
        ax2.set_ylabel("VMA (%)")
        st.pyplot(fig2)

        fig3, ax3 = plt.subplots()
        ax3.plot(df['Bitumen Content (%)'], df['VFB (%)'], marker='^', color='red')
        ax3.set_title("VFB vs. Bitumen Content")
        ax3.set_xlabel("Bitumen Content (%)")
        ax3.set_ylabel("VFB (%)")
        st.pyplot(fig3)

        # Excel Download
        excel_data = generate_excel_download(df)
        st.markdown(download_link(excel_data, 'bitumen_mix_analysis.xlsx', '📥 Download Results as Excel'), unsafe_allow_html=True)