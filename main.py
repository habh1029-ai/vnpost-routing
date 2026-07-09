import streamlit as st
import folium
from folium.plugins import Fullscreen
import requests
import pandas as pd
from streamlit_folium import st_folium

st.set_page_config(page_title="VNPOST Logistics", layout="wide")

st.markdown(
    """<style>
    .main-title { font-size: 2rem; font-weight: 800; color: #0056b3; border-bottom: 4px solid #F2A900; padding-bottom: 10px; }
    .metric-card { background: #f8fafc; border-left: 5px solid #F2A900; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    div.stButton > button { background: #F2A900; color: #003366!important; font-weight: bold; width: 100%; }
    .status-delivery { background-color: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .status-success { background-color: #dcfce7; color: #15803d; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .status-pending { background-color: #fef3c7; color: #b45309; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .timeline-item { border-left: 3px solid #0056b3; padding-left: 15px; margin-bottom: 15px; position: relative; }
    .timeline-time { font-size: 0.85rem; color: #64748b; font-weight: bold; }
    </style>""", 
    unsafe_allow_html=True
)

# Tách biệt hàm xử lý API để chống lỗi lồng khối try-except phức tạp
def get_osrm_trip(coord_str):
    try:
        url = f"http://router.project-osrm.org/trip/v1/driving/{coord_str}?source=first&destination=any&overview=full&geometries=geojson"
        res = requests.get(url, timeout=5).json()
        return res
    except:
        return None

VNPOST_HUBS = {
    "Bưu cục Tân Định (Q1)": {"address": "230 Hai Bà Trưng, Q1", "lat": 10.7891, "lon": 106.6910},
    "Bưu cục Giao dịch Sài Gòn (Q1)": {"address": "2 Công xã Paris, Q1", "lat": 10.7798, "lon": 106.6999},
    "Bưu cục Quận 3": {"address": "2Bis Bà Huyện Thanh Quan, Q3", "lat": 10.7770, "lon": 106.6853},
    "Bưu cục Bàn Cờ (Q3)": {"address": "49A Cao Thắng, Q3", "lat": 10.7745, "lon": 106.6811},
    "Bưu cục Quận 5": {"address": "26 Nguyễn Thị, Q5", "lat": 10.7512, "lon": 106.6631},
    "Bưu cục Quận 7": {"address": "1441 Huỳnh Tấn Phát, Q7", "lat": 10.7351, "lon": 106.7323}
}

POPULAR_STOPS = {
    "120 cách mạng tháng tám": [10.7792, 106.6881], "240 điện biên phủ": [10.7865, 106.6915],
    "312 võ thị sáu": [10.7849, 106.6872], "02 võ oanh": [10.8021, 106.7142],
    "100 cao thắng": [10.7745, 106.6811], "320 nguyễn du": [10.7712, 106.6945],
    "hồ con rùa":
