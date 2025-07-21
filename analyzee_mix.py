import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import xlsxwriter

st.set_page_config(page_title="Bitumen Mix Analyzer", layout="wide")
st.title("🛣️ Bitumen Mix Volumetric Analyzer")

st.markdown("Upload your Excel file with these required columns: `Sample`, `Bitumen Content (%)`, `Gmb`, `Gmm`")

uploaded_file = st.file_uploader("📂 Upload Excel File", type=[".xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("File uploaded successfully!")
    st.write("### Preview of Uploaded Data")
    st.dataframe(df)

    # User inputs
    Gb = st.number_input("Enter Specific Gravity of Binder (Gb):", min_value=0.0, step=0.01, format="%.3f")
    Gsb = st.number_input("Enter Bulk Specific Gravity of Aggregate (Gsb):", min_value=0.0, step=0.01, format="%.3f")

    if Gb > 0 and Gsb > 0:
        df["Va (%)"] = ((df["Gmm"] - df["Gmb"]) / df["Gmm"]) * 100
        df["VMA (%)"] = (1 - df["Gmb"] / Gsb) * 100
        df["VFB (%)"] = ((df["VMA (%)"] - df["Va (%)"]) / df["VMA (%)"]) * 100

        df["Va Status"] = df["Va (%)"].apply(lambda x: "✅" if 3 <= x <= 5 else "❌")
        df["VMA Status"] = df["VMA (%)"].apply(lambda x: "✅" if x >= 14 else "❌")
        df["VFB Status"] = df["VFB (%)"].apply(lambda x: "✅" if 65 <= x <= 75 else "❌")

        # Remove duplicate columns if any
        df = df.loc[:, ~df.columns.duplicated()]

        st.write("### Computed Results")
        st.dataframe(df)

        # Plotting
        st.write("### 📊 Graphs")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["Bitumen Content (%)"], df["Va (%)"], marker='o', label="Air Voids (Va)")
        ax.plot(df["Bitumen Content (%)"], df["VMA (%)"], marker='s', label="VMA")
        ax.plot(df["Bitumen Content (%)"], df["VFB (%)"], marker='^', label="VFB")
        ax.set_xlabel("Bitumen Content (%)")
        ax.set_ylabel("% Value")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # Export to Excel with graph
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Results')
            workbook = writer.book
            worksheet = writer.sheets['Results']

            img_data = io.BytesIO()
            fig.savefig(img_data, format='png')
            img_data.seek(0)

            worksheet.insert_image("K2", "graph.png", {'image_data': img_data, 'x_scale': 0.7, 'y_scale': 0.7})

        output.seek(0)
        st.download_button("📥 Download Excel with Graph", data=output,
                           file_name="bitumen_mix_analysis.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    else:
        st.warning("Please enter both Gb and Gsb to continue.")