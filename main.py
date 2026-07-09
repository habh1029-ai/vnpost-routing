import streamlit as st
import folium
import math
import requests
import pandas as pd
from streamlit_folium import folium_static

# 1. CẤU HÌNH GIAO DIỆN WEB TOÀN MÀN HÌNH
st.set_page_config(
    page_title="VNPOST - Điều hành Logistics Đa điểm", 
    layout="wide"
)

# 2. CHÈN CSS CUSTOM ĐỂ TRANG TRÍ WEB (MÀU SẮC ĐẬM CHẤT VIETNAM POST)
st.markdown("""
    <style>
        .main-title {
            font-size: 2rem !important;
            font-weight: 800;
            color: #0056b3;
            text-transform: uppercase;
            border-bottom: 4px solid #F2A900;
            padding-bottom: 10px;
            margin-bottom: 5px;
        }
        .metric-card {
            background: #f8fafc;
            border-left: 5px solid #F2A900;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }
        div.stButton > button:first-child {
            background: #F2A900;
            color: #003366 !important;
            font-weight: bold !important;
            border: none;
            border-radius: 6px;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# 3. CƠ SỞ DỮ LIỆU BƯU CỤC VNPOST TP.HCM (ĐÃ TÍCH HỢP TỌA ĐỘ CỨNG TRÁNH LỖI API)
VNPOST_HUBS = {
    "Bưu cục Tân Định (Q1)": {"address": "230 Hai Bà Trưng, Quận 1", "lat": 10.7891, "lon": 106.6910},
    "Bưu cục Giao dịch Sài Gòn (Q1)": {"address": "2 Công xã Paris, Quận 1", "lat": 10.7798, "lon": 106.6999},
