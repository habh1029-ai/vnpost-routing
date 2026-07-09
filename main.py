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

# 2. CHÈN CSS CUSTOM ĐỂ TRANG TRÍ WEB (ĐẬM BẢN SẮC VIETNAM POST)
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

# 3. CƠ SỞ DỮ LIỆU BƯU CỤC VNPOST TP.HCM
VNPOST_HUBS = {
    "Bưu cục Tân Định (Q1)": "230 Hai Bà Trưng, Quận 1",
    "Bưu cục Giao dịch Sài Gòn (Q1)": "2 Công xã Paris, Quận 1",
    "Bưu cục Quận 3": "2Bis Bà Huyện Thanh Quan, Quận 3",
    "Bưu cục Bàn Cờ (Q3)": "49A Cao Thắng, Quận 3",
    "Bưu cục Quận 5": "26 Nguyễn Thị, Quận 5",
    "Bưu cục Quận 7": "1441 Huỳnh Tấn Phát, Quận 7"
}

# 4. DỮ LIỆU THỐNG KÊ (MOCK DATA)
DISTRICT_DATA = {
    "Thành công": [420, 380, 290, 180, 150],
    "Hoàn lại": [15, 22, 12, 8, 19]
}
DISTRICT_INDEX = ["Quận 1", "Quận 3", "Quận 5", "Quận 7", "Quận 4"]

WEIGHT_DATA = {
    "Xe máy": [2.1, 2.8, 3.2, 2.9, 3.5, 4.1, 1.5],
    "Xe tải": [8.5, 9.2, 11.0, 10.1, 12.4, 14.0, 5.0]
}
WEIGHT_INDEX = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

MOCK_ORDERS = {
    "Mã Vận Đơn":
