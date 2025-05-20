import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from urllib.parse import urljoin

# Настройка стилей
st.set_page_config(
    page_title="📡 Трансформатор координат", 
    layout="wide",
    page_icon="🌐"
)

# Кастомный CSS
st.markdown("""
<style>
    .header-style { color: #2E86C1; font-family: 'Arial'; }
    .stButton>button { background: #1ABC9C; color: white; border-radius: 8px; }
    .stSelectbox>div>div>div { border: 2px solid #3498DB; }
    .stFileUploader>section>div { border: 2px dashed #28B463; }
    .report-output { background: #F9E79F; padding: 15px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

API_SERVICE = "https://prac10-i54v.onrender.com"

COORDINATE_SYSTEMS = {
    "СК-42": "russian42",
    "ПЗ-90.11": "pz9011",
    "WGS84_G1150": "wgs84",
    "ГСК-2011": "gsk2011",
    "ITRF-2008": "itrf08",
    "СК-95": "russian95",
    "ПЗ-90": "pz90",
    "ПЗ-90.02": "pz9002"
}

def display_guide():
    with st.expander("📘 Инструкция по использованию"):
        st.markdown("""
        1. Загрузите файл в формате CSV/XLSX
        2. Проверьте предпросмотр данных
        3. Выберите системы координат
        4. Нажмите соответствующую кнопку преобразования
        5. Скачайте результат
        
        **Требования к данным:**
        - Обязательные колонки: Name, X, Y, Z
        - Поддерживаемые форматы: .csv, .xlsx
        """)

def transform_data(file, source_system, target_system):
    url = urljoin(API_SERVICE, "/convert-coordinates/")
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {"source_system": source_system, "target_system": target_system}
    try:
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            st.error(f"Ошибка: {response.text}")
            return None
    except Exception as e:
        st.error(f"Ошибка связи с API: {str(e)}")
        return None

def generate_markdown_report(file, source_system, target_system):
    url = urljoin(API_SERVICE, "/generate-report/")
    files = {"file": (file.name, file.getvalue(), file.type)}
    data = {"source_system": source_system, "target_system": target_system}
    try:
        response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            st.error(f"Ошибка: {response.text}")
            return None
    except Exception as e:
        st.error(f"Ошибка связи с API: {str(e)}")
        return None

def main_interface():
    st.markdown("<h1 class='header-style'>📡 Трансформатор геопространственных данных</h1>", unsafe_allow_html=True)
    
    display_guide()
    
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Перетащите файл с координатами", 
            type=["csv", "xlsx"],
            help="Поддерживаются CSV и Excel файлы с координатами"
        )

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.type == "text/csv" else pd.read_excel(uploaded_file)
            
            if not {"Name", "X", "Y", "Z"}.issubset(df.columns):
                st.error("❌ Неверная структура файла!")
                return

            with st.container():
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.subheader("Параметры преобразования")
                    src_sys = st.selectbox(
                        "Исходная система", 
                        options=list(COORDINATE_SYSTEMS.keys()),
                        index=3
                    )
                    tgt_sys = st.selectbox(
                        "Целевая система", 
                        options=list(COORDINATE_SYSTEMS.keys()),
                        index=5
                    )
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("🔄 Конвертировать", use_container_width=True):
                            with st.spinner("Трансформация координат..."):
                                result = transform_data(uploaded_file, src_sys, tgt_sys)
                                if result:
                                    st.session_state.converted_data = result
                    with c2:
                        if st.button("📊 Создать отчет", type="secondary", use_container_width=True):
                            with st.spinner("Формирование отчёта..."):
                                report_data = generate_markdown_report(uploaded_file, src_sys, tgt_sys)
                            if report_data:
                                st.download_button(
                                    label="⬇️ Скачать Markdown-отчет",
                                    data=report_data,
                                    file_name="report.md",
                                    mime="text/markdown"
                                )

                with col2:
                    st.subheader("Структура данных")
                    st.dataframe(
                        df.head(5).style.highlight_max(color="#F8C471").format(precision=3),
                        use_container_width=True
                    )

            if "converted_data" in st.session_state:
                st.divider()
                st.success("✅ Преобразование завершено!")
                st.download_button(
                    label="💾 Скачать результат",
                    data=st.session_state.converted_data,
                    file_name="transformed_coordinates.csv",
                    mime="text/csv",
                    type="primary"
                )

        except Exception as e:
            st.error(f"Критическая ошибка: {str(e)}")

if __name__ == "__main__":
    main_interface()