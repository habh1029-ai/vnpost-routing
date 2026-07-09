import streamlit as st
import folium
import math
import requests
import pandas as pd
from streamlit_folium import folium_static

# 1. CẤU HÌNH GIAO DIỆN WEB TOÀN MÀN HÌNH & GIAO DIỆN HIỆN ĐẠI
st.set_page_config(
    page_title="Hệ thống Điều hành Bưu chính Vietnam Post", 
    layout="wide",
    initial_sidebar_state="collapsed" # Mặc định thu gọn sidebar để ưu tiên hiển thị di động
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

# CƠ SỞ DỮ LIỆU BƯU CỤC VNPOST TP.HCM ĐÃ ĐƯỢC LÀM SẠCH CHỮ QUẬN
VNPOST_HUBS = {
    "Bưu cục Giao dịch Sài Gòn": "2 Công xã Paris, Quận 1",
    "Bưu cục Giao Dịch Quốc Tế Sài Gòn": "117 Hai Bà Trưng, Quận 1",
    "Bưu cục Tân Định": "230 Hai Bà Trưng, Quận 1",
    "Bưu cục Trần Hưng Đạo": "447B Trần Hưng Đạo, Quận 1",
    "Bưu cục Quận 3": "2Bis Bà Huyện Thanh Quan, Quận 3",
    "Bưu cục Bàn Cờ": "49A Cao Thắng, Quận 3",
    "Bưu cục Vườn Xoài": "472 Lê Văn Sỹ, Quận 3",
    "Bưu cục Quận 4": "104 Nguyễn Tất Thành, Quận 4",
    "Bưu cục Khánh Hội": "52 Lê Quốc Hưng, Quận 4",
    "Bưu cục Nguyễn Trãi": "49 Nguyễn Trãi, Quận 5",
    "Bưu cục Quận 5": "26 Nguyễn Thi, Quận 5",
    "Bưu cục Quận 6": "88 Tháp Mười, Quận 6",
    "Bưu cục Tân Phong": "565 Nguyễn Thị Thập, Quận 7",
    "Bưu cục Quận 7": "1441 Huỳnh Tấn Phát, Quận 7"
}

def get_coordinates_from_address(address_text):
    try:
        full_query = f"{address_text}, Ho Chi Minh City, Vietnam"
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(full_query)}&format=json&limit=1"
        headers = {"User-Agent": "vietnam_post_routing_app_2026"}
        response = requests.get(url, headers=headers, timeout=10).json()
        if response:
            return {"lat": float(response[0]["lat"]), "lon": float(response[0]["lon"]), "display_name": response[0]["display_name"].split(",")[0]}
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
        if 25 <= turn < 155: instructions.append("↩️ **Rẽ phải** tại giao lộ tiếp theo.")
        elif 205 <= turn < 335: instructions.append("↪️ **Rẽ trái** vào tuyến đường phân phối.")
    instructions.append("🔴 **Đến nơi:** Địa điểm bàn giao hàng nằm phía trước.")
    return instructions[:6]

# BANNER TIÊU ĐỀ TRÊN CÙNG
st.markdown('<p class="main-title">✉️ HỆ THỐNG ĐIỀU HÀNH BƯU CHÍNH THÔNG MINH VIETNAM POST</p>', unsafe_allow_html=True)

tab_enterprise, tab_routing, tab_status = st.tabs([
    "🏢 Trung tâm Giám sát", 
    "🗺️ Tối ưu Tuyến đường", 
    "📦 Quản lý Vận đơn"
])

# ------------------------------------------
# TAB 1: TRUNG TÂM GIÁM SÁT DOANH NGHIỆP
# ------------------------------------------
with tab_enterprise:
    st.markdown("### 📊
