import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from urllib.parse import urljoin

st.set_page_config(page_title="🛰️ Системы координат", layout="centered")

API_ENDPOINT = "https://prac10-i54v.onrender.com"

SYSTEM_OPTIONS = [
    "СК-95", "ПЗ-90.11", "WGS-84 (G1150)",
    "СК-42", "ITRF-2008", "ПЗ-90", 
    "ГСК-2011", "ПЗ-90.02"
]

def api_available():
    try:
        return requests.head(API_ENDPOINT, timeout=7).status_code == 200
    except:
        return False

def process_coordinates(data_file, from_system, to_system):
    service_url = urljoin(API_ENDPOINT, "/transform/")
    upload = {"data_file": (data_file.name, data_file.getvalue(), data_file.type)}
    params = {"from": from_system, "to": to_system}
    
    try:
        result = requests.post(service_url, files=upload, data=params)
        return BytesIO(result.content) if result.ok else None
    except:
        st.error("Сервис временно недоступен")
        return None

def create_md_report(data_file, from_system, to_system):
    report_url = urljoin(API_ENDPOINT, "/analysis/")
    upload = {"data_file": (data_file.name, data_file.getvalue(), data_file.type)}
    params = {"from": from_system, "to": to_system}
    
    try:
        response = requests.post(report_url, files=upload, data=params)
        return BytesIO(response.content) if response.ok else None
    except:
        st.error("Ошибка генерации отчёта")
        return None

def app_interface():
    st.header("Преобразование пространственных координат")
    st.caption("Загрузите табличный файл для конвертации значений")
    
    # if not api_available():
    #     st.warning("Сервис обработки недоступен")
    #     return

    data_input = st.file_uploader("Исходные данные", ["csv", "xls", "xlsx"])
    
    if data_input:
        try:
            df = pd.read_csv(data_input) if data_input.type == "text/csv" else pd.read_excel(data_input)
            
            if {"X", "Y", "Z", "Name"}.issubset(df.columns):
                st.subheader("Первые записи")
                st.write(df.sample(min(3, len(df))))
                
                data_input.seek(0)
                
                left, right = st.columns(2)
                with left:
                    src = st.selectbox("Исходная СК", SYSTEM_OPTIONS, index=3)
                with right:
                    dst = st.selectbox("Целевая СК", SYSTEM_OPTIONS, index=5)
                
                if st.button("Выполнить преобразование"):
                    with st.status("Обработка..."):
                        output = process_coordinates(data_input, src, dst)
                        if output:
                            st.download_button(
                                "Экспорт результатов",
                                output,
                                "converted_data.csv",
                                "text/csv"
                            )
                
                if st.button("Создать аналитику"):
                    with st.spinner("Подготовка отчёта..."):
                        md_report = create_md_report(data_input, src, dst)
                        if md_report:
                            st.download_button(
                                "Скачать отчёт",
                                md_report,
                                "coord_report.md",
                                "text/markdown"
                            )
            else:
                st.error("Неверная структура данных: требуются колонки Name, X, Y, Z")
        
        except Exception as error:
            st.error(f"Ошибка обработки файла: {str(error)}")

if __name__ == "__main__":
    app_interface()