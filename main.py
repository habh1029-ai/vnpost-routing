import streamlit as st
import folium
import math
import requests
import pandas as pd
from streamlit_folium import folium_static

# 1. CẤU HÌNH GIAO DIỆN WEB TOÀN MÀN HÌNH
st.set_page_config(
    page_title="Hệ thống Điều hành Bưu chính Vietnam Post", 
    layout="wide"
)

# 2. CHÈN CSS CUSTOM ĐỂ TRANG TRÍ WEB SINH ĐỘNG (NHẬN DIỆN VNPOST)
st.markdown("""
    <style>
        .main-title {
            font-size: 2.1rem !important;
            font-weight: 800;
            color: #0056b3;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
            border-bottom: 4px solid #F2A900;
            padding-bottom: 10px;
        }
        .metric-card {
            background: linear-gradient(145deg, #ffffff, #f1f5f9);
            border-left: 5px solid #F2A900;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 15px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #f1f5f9;
            border-radius: 8px 8px 0px 0px;
            padding: 10px 16px;
            font-weight: bold;
            color: #475569;
        }
        .stTabs [aria-selected="true"] {
            background-color: #0056b3 !important;
            color: white !important;
            border-bottom: 3px solid #F2A900 !important;
        }
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #F2A900, #ffc745);
            color: #003366 !important;
            font-weight: bold !important;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            box-shadow: 0 4px 10px rgba(242,169,0,0.3);
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# CƠ SỞ DỮ LIỆU BƯU CỤC VNPOST TP.HCM
VNPOST_HUBS = {
    "Bưu cục Tân Định (Q1)": "230 Hai Ba Trung, Quan 1",
    "Bưu cục Giao dịch Sài Gòn (Q1)": "2 Cong xa Paris, Quan 1",
    "Bưu cục Giao Dịch Quốc Tế Sài Gòn": "117 Hai Ba Trung, Quan 1",
    "Bưu cục Trần Hưng Đạo (Q1)": "447B Tran Hung Dao, Quan 1",
    "Bưu cục Quận 3": "2Bis Ba Huyen Thanh Quan, Quan 3",
    "Bưu cục Bàn Cờ (Q3)": "49A Cao Thang, Quan 3",
    "Bưu cục Vườn Xoài (Q3)": "472 Le Van Sy, Quan 3",
    "Bưu cục Quận 4": "104 Nguyen Tat Thanh, Quan 4",
    "Bưu cục Khánh Hội (Q4)": "52 Le Quoc Hung, Quan 4",
    "Bưu cục Nguyễn Trãi (Q5)": "49 Nguyen Trai, Quan 5",
    "Bưu cục Quận 5": "26 Nguyen Thi, Quan 5",
    "Bưu cục Quận 6": "88 Thap Muoi, Quan 6",
    "Bưu cục Tân Phong (Q7)": "565 Nguyen Thi Thap, Quan 7",
    "Bưu cục Quận 7": "1441 Huynh Tan Phat, Quan 7"
}

def get_coordinates_from_address(address_text):
    try:
        full_query = f"{address_text}, Ho Chi Minh City, Vietnam"
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(full_query)}&format=json&limit=1"
        headers = {"User-Agent": "vietnam_post_routing_app_2026"}
        response = requests.get(url, headers=headers, timeout=10).json()
        if response:
            return {
                "lat": float(response[0]["lat"]), 
                "lon": float(response[0]["lon"]), 
                "display_name": response[0]["display_name"].split(",")[0]
            }
        return None
    except Exception:
        return None

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lon = lon2_rad - lon1_rad
    x = math.sin(d_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - (math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(d_lon))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def generate_turn_by_turn(geometry_coords):
    if len(geometry_coords) < 3:
        return ["🟢 Xuất phát: Di chuyển thẳng theo lộ trình."]
    instructions = ["🟢 **Xuất phát:** Khởi hành từ bưu cục, bám sát lòng đường hành trình."]
    sample_rate = max(1, len(geometry_coords) // 6)
    for i in range(sample_rate, len(geometry_coords) - sample_rate, sample_rate):
        p1, p2, p3 = geometry_coords[i - sample_rate], geometry_coords[i], geometry_coords[i + sample_rate]
        turn = (calculate_bearing(p2[0], p2[1], p3[0], p3[1]) - calculate_bearing(p1[0], p1[1], p2[0], p2[1]) + 360) % 360
        if 25 <=
