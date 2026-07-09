import streamlit as st
import folium
import math
import requests
import pandas as pd
from streamlit_folium import folium_static

# 1. CẤU HÌNH GIAO DIỆN WEB TOÀN MÀN HÌNH
st.set_page_config(
    page_title="Hệ thống Điều hành Bưu chính Vietnam Post - Tuyến đa điểm", 
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

# KHỞI TẠO DỮ LIỆU MOCK DATA BAN ĐẦU
DISTRICT_DATA = {
    "Thành công (Đã ký POD)": [420, 380, 290, 180, 150],
    "Đang phát/Hoãn lại": [15, 22, 12, 8, 19]
}
DISTRICT_INDEX = ["Quận 1", "Quận 3", "Quận 5", "Quận 7", "Quận 4"]

WEIGHT_DATA = {
    "Đội xe máy chặng cuối": [2.1, 2.8, 3.2, 2.9, 3.5, 4.1, 1.5],
    "Đội xe tải bưu chính": [8.5, 9.2, 11.0, 10.1, 12.4, 14.0, 5.0]
}
WEIGHT_INDEX = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

MOCK_ORDERS = {
    "Mã Vận Đơn": ["VN94827HCM", "VN10482HCM", "VN58291HCM", "VN30294HCM"],
    "Người Nhận": ["Nguyễn Văn A", "Trần Thị B", "Lê Hoàng C", "Phạm Minh D"],
    "Địa Chỉ": ["100 Cao Thắng, Q3", "320 Nguyễn Du, Q1", "Hồ Con Rùa, Q3", "Vòng xoay Dân Chủ"],
    "Loại Hàng": ["Tài liệu mật", "Linh kiện điện tử", "Bưu kiện lớn", "Hàng dễ vỡ"]
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
    st.markdown("### 🛠
