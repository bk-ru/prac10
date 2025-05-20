import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from urllib.parse import urljoin

# Настройки страницы
st.set_page_config(
    page_title="🌐 Трансформатор геопозиций", 
    layout="centered",
    menu_items={
        'About': "Инструмент для преобразования координат между разными системами"
    }
)

# Конфигурация API
API_ENDPOINT = "https://prac10-i54v.onrender.com"

# Доступные системы координат
COORDINATE_SYSTEMS = {
    "СК-42": "СК-42",
    "СК-95": "СК-95", 
    "ПЗ-90": "ПЗ-90",
    "ПЗ-90.02": "ПЗ-90.02",
    "ПЗ-90.11": "ПЗ-90.11",
    "WGS-84": "WGS-84 (G1150)",
    "ITRF-2008": "ITRF-2008",
    "ГСК-2011": "ГСК-2011"
}

def verify_api_connection():
    """Проверяет доступность API сервера"""
    try:
        response = requests.get(API_ENDPOINT, timeout=5)
        return response.ok
    except requests.exceptions.RequestException:
        return False

def process_coordinate_conversion(file_obj, src_system, dst_system):
    """Отправляет файл на сервер для преобразования координат"""
    api_url = urljoin(API_ENDPOINT, "/convert-coordinates/")
    file_data = {"file": (file_obj.name, file_obj.getvalue(), file_obj.type)}
    params = {"source_system": src_system, "target_system": dst_system}
    
    try:
        api_response = requests.post(api_url, files=file_data, data=params)
        if api_response.status_code == 200:
            return BytesIO(api_response.content)
        st.warning(f"Сервер вернул ошибку: {api_response.text}")
    except Exception as api_error:
        st.error(f"Проблемы с соединением: {api_error}")
    return None

def create_markdown_document(file_obj, src_system, dst_system):
    """Генерирует отчёт в формате Markdown"""
    report_url = urljoin(API_ENDPOINT, "/generate-report/")
    file_data = {"file": (file_obj.name, file_obj.getvalue(), file_obj.type)}
    params = {"source_system": src_system, "target_system": dst_system}
    
    try:
        response = requests.post(report_url, files=file_data, data=params)
        if response.status_code == 200:
            return BytesIO(response.content)
        st.warning(f"Ошибка генерации отчёта: {response.text}")
    except Exception as report_error:
        st.error(f"Ошибка при создании отчёта: {report_error}")
    return None

def display_file_preview(uploaded_file):
    """Отображает превью загруженного файла"""
    try:
        if uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file)
        else:
            data = pd.read_excel(uploaded_file)
        
        required_fields = ["Name", "X", "Y", "Z"]
        if not all(field in data.columns for field in required_fields):
            st.error(f"Необходимые колонки: {', '.join(required_fields)}")
            return False
            
        st.subheader("Предпросмотр данных")
        st.dataframe(data.head(3))
        return True
        
    except Exception as parse_error:
        st.error(f"Ошибка чтения файла: {parse_error}")
        return False

def main_interface():
    """Основной интерфейс приложения"""
    st.header("🌍 Конвертер систем координат")
    st.caption("Загрузите файл с координатами для преобразования между системами")
    
    # Проверка подключения к API
    if not verify_api_connection():
        st.warning("Сервис временно недоступен. Попробуйте позже.")
        return
    
    # Загрузка файла
    input_file = st.file_uploader(
        "Выберите файл с координатами", 
        type=['csv', 'xlsx'],
        accept_multiple_files=False
    )
    
    if not input_file:
        return
        
    if not display_file_preview(input_file):
        return
        
    # Выбор систем координат
    col_left, col_right = st.columns(2)
    with col_left:
        source_crs = st.selectbox(
            "Исходная система координат",
            options=list(COORDINATE_SYSTEMS.keys())
        )
    with col_right:
        target_crs = st.selectbox(
            "Целевая система координат",
            options=list(COORDINATE_SYSTEMS.keys())
        )
    
    # Кнопки действий
    if st.button("🔄 Конвертировать", type="primary"):
        with st.spinner("Идёт преобразование..."):
            result = process_coordinate_conversion(input_file, source_crs, target_crs)
            if result:
                st.success("Готово!")
                st.download_button(
                    "💾 Сохранить результат",
                    data=result,
                    file_name="converted_coords.csv",
                    mime="text/csv"
                )
    
    if st.button("📊 Создать отчёт"):
        with st.spinner("Формирование документа..."):
            report = create_markdown_document(input_file, source_crs, target_crs)
            if report:
                st.success("Отчёт подготовлен!")
                st.download_button(
                    "📥 Загрузить отчёт",
                    data=report,
                    file_name="coordinate_report.md",
                    mime="text/markdown"
                )

if __name__ == "__main__":
    main_interface()