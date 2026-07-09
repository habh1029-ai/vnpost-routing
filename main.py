import streamlit as st
import folium
import math
import requests
import pandas as pd
from streamlit_folium import folium_static

# 1. CẤU HÌNH GIAO DIỆN WEB TOÀN MÀN HÌNH
st.set_page_config(
    page_title="He thong Dieu hanh Buu chinh Vietnam Post - Tuyen da diem", 
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
    "Buu cuc Tan Dinh (Q1)": "230 Hai Ba Trung, Quan 1",
    "Buu cuc Giao dich Sai Gon (Q1)": "2 Cong xa Paris, Quan 1",
    "Buu cuc Giao Dich Quoc Te Sai Gon": "117 Hai Ba Trung, Quan 1",
    "Buu cuc Tran Hung Dao (Q1)": "447B Tran Hung Dao, Quan 1",
    "Buu cuc Quan 3": "2Bis Ba Huyen Thanh Quan, Quan 3",
    "Buu cuc Ban Co (Q3)": "49A Cao Thang, Quan 3",
    "Buu cuc Vuon Xoai (Q3)": "472 Le Van Sy, Quan 3",
    "Buu cuc Quan 4": "104 Nguyen Tat Thanh, Quan 4",
    "Buu cuc Khanh Hoi (Q4)": "52 Le Quoc Hung, Quan 4",
    "Buu cuc Nguyen Trai (Q5)": "49 Nguyen Trai, Quan 5",
    "Buu cuc Quan 5": "26 Nguyen Thi, Quan 5",
    "Buu cuc Quan 6": "88 Thap Muoi, Quan 6",
    "Buu cuc Tan Phong (Q7)": "565 Nguyen Thi Thap, Quan 7",
    "Buu cuc Quan 7": "1441 Huynh Tan Phat, Quan 7"
}

# KHỞI TẠO DỮ LIỆU MOCK DATA BAN ĐẦU
DISTRICT_DATA = {
    "Thanh cong (Da ky POD)": [420, 380, 290, 180, 150],
    "Dang phat/Hoan lai": [15, 22, 12, 8, 19]
}
DISTRICT_INDEX = ["Quan 1", "Quan 3", "Quan 5", "Quan 7", "Quan 4"]

WEIGHT_DATA = {
    "Doi xe may chang cuoi": [2.1, 2.8, 3.2, 2.9, 3.5, 4.1, 1.5],
    "Doi xe tai buu chinh": [8.5, 9.2, 11.0, 10.1, 12.4, 14.0, 5.0]
}
WEIGHT_INDEX = ["Thu 2", "Thu 3", "Thu 4", "Thu 5", "Thu 6", "Thu 7", "Chu Nhat"]

MOCK_ORDERS = {
    "Ma Van Don": ["VN94827HCM", "VN10482HCM", "VN58291HCM", "VN30294HCM"],
    "Nguoi Nhan": ["Nguyen Van A", "Tran Thi B", "Le Hoang C", "Pham Minh D"],
    "Dia Chi": ["100 Cao Thang, Q3", "320 Nguyen Du, Q1", "Ho Con Rua, Q3", "Vong xoay Dan Chu"],
    "Loai Hang": ["Tai lieu mat", "Linh kien dien tu", "Buu kien lon", "Hang de vo"]
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

# 3. SIDEBAR CẤU HÌNH TUYẾN ĐƯỜNG ĐA ĐIỂM
with st.sidebar:
    st.write("### Cau hinh Lo trinh Da Diem")
    selected_start_hub = st.selectbox("Chon nhanh buu cuc xuat phat:", list(VNPOST_HUBS.keys()))
    start_input = st.text_area("Tu buu cuc (Diem xuat phat):", value=VNPOST_HUBS[selected_start_hub], height=70)
    
    st.write("---")
    st.write("Danh sach cac diem giao hang (Multi-drop):")
    st.caption("Nhap danh sach dia chi, moi dia chi viet tren 1 dong theo thu tu giao uu tien:")
    
    default_stops = "100 Cao Thang, Quan 3\n320 Nguyen Du, Quan 1\nHo Con Rua, Quan 3"
    stops_input = st.text_area("Cac diem giao hang chang cuoi:", value=default_stops, height=130)
    
    st.write("---")
    st.write("Phuong tien van chuyen:")
    vehicle_type = st.radio(
        "Lua chon phuong tien:",
        ["Xe may buu ta chang cuoi", "Xe tai buu chinh lon"],
        label_visibility="collapsed"
    )
    
    activated = st.button("TINH TOAN LO TRINH THUC DIA")

# TIÊU ĐỀ CHÍNH TRANG WEB
st.markdown("""<p class="main-title">HE THONG DIEU HANH BUU CHINH THONG MINH VIETNAM POST</p>""", unsafe_allow_html=True)
st.write("*Truc quan hoa mang luoi Logistics, Dinh tuy
