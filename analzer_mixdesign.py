# analyze_mix.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import xlsxwriter
import numpy as np

st.set_page_config(page_title="Bitumen Mix Analyzer", layout="centered")
st.title("🛣️ Bitumen Mix Analyzer")
st.markdown("Upload your Excel file with mix data to analyze volumetric properties.")

uploaded_file = st.file_uploader("Upload Excel File", type=[".xlsx"])

def calculate_properties(df, Gb, Gsb):
    df['Va (%)'] = ((df['Gmm'] - df['Gmb']) / df['Gmm']) * 100
    df['VMA (%)'] = 100 - (df['Gmb'] / Gsb) * (100 - df['Bitumen Content (%)'])
    df['VFB (%)'] = ((df['VMA (%)'] - df['Va (%)']) / df['VMA (%)']) * 100
    return df

def evaluate_specs(df):
    df['Va Status'] = df['Va (%)'].apply(lambda x: '✔️' if 3 <= x <= 5 else '❌')
    df['VMA Status'] = df['VMA (%)'].apply(lambda x: '✔️' if x >= 14 else '❌')
    df['VFB Status'] = df['VFB (%)'].apply(lambda x: '✔️' if 65 <= x <= 82 else '❌')
    return df

def plot_relation_to_buffer(x, y, xlabel, ylabel, title, color='blue', degree=2):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(x, y, color=color, label='Data')
    if len(x.dropna()) > degree:
        coeffs = np.polyfit(x, y, degree)
        x_sorted = np.sort(x)
        y_fit = np.polyval(coeffs, x_sorted)
        ax.plot(x_sorted, y_fit, color='black', linestyle='--', label=f'Trend (deg {degree})')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf

def generate_excel_download(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Results')
        workbook = writer.book
        worksheet = writer.sheets['Results']

        # Insert charts with xlsxwriter
        charts = [
            ('VMA vs Bitumen Content', 'Bitumen Content (%)', 'VMA (%)', 'L2'),
            ('VFB vs Bitumen Content', 'Bitumen Content (%)', 'VFB (%)', 'L20'),
            ('Air Voids vs Bitumen Content', 'Bitumen Content (%)', 'Va (%)', 'L38')
        ]

        for title, x_col, y_col, location in charts:
            chart = workbook.add_chart({'type': 'scatter', 'subtype': 'straight_with_markers'})
            chart.add_series({
                'name':       title,
                'categories': ['Results', 1, df.columns.get_loc(x_col), len(df), df.columns.get_loc(x_col)],
                'values':     ['Results', 1, df.columns.get_loc(y_col), len(df), df.columns.get_loc(y_col)],
            })
            chart.set_title({'name': title})
            chart.set_x_axis({'name': x_col})
            chart.set_y_axis({'name': y_col})
            worksheet.insert_chart(location, chart)

    processed_data = output.getvalue()
    return processed_data

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

        df = df.sort_values(by='Bitumen Content (%)')

        st.subheader("Graphs")
        for title, y_col, color in [
            ("Air Voids vs. Bitumen Content", 'Va (%)', 'blue'),
            ("VMA vs. Bitumen Content", 'VMA (%)', 'green'),
            ("VFB vs. Bitumen Content", 'VFB (%)', 'red')
        ]:
            buffer = plot_relation_to_buffer(df['Bitumen Content (%)'], df[y_col], 'Bitumen Content (%)', y_col, title, color)
            st.image(buffer, caption=title)

        excel_data = generate_excel_download(df)
        st.markdown(download_link(excel_data, 'bitumen_mix_analysis.xlsx', '📥 Download Results as Excel'), unsafe_allow_html=True)
