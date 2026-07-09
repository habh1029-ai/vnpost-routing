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

def get_osrm_trip(coord_str):
    try:
        url = f"http://router.project-osrm.org/trip/v1/driving/{coord_str}?source=first&destination=any&overview=full&geometries=geojson"
        return requests.get(url, timeout=5).json()
    except:
        return None

# Dữ liệu hệ thống dòng đơn chống lỗi bẻ dòng
VNPOST_HUBS = {"Bưu cục Tân Định (Q1)": {"address": "230 Hai Bà Trưng, Q1", "lat": 10.7891, "lon": 106.6910}, "Bưu cục Giao dịch Sài Gòn (Q1)": {"address": "2 Công xã Paris, Q1", "lat": 10.7798, "lon": 106.6999}, "Bưu cục Quận 3": {"address": "2Bis Bà Huyện Thanh Quan, Q3", "lat": 10.7770, "lon": 106.6853}, "Bưu cục Bàn Cờ (Q3)": {"address": "49A Cao Thắng, Q3", "lat": 10.7745, "lon": 106.6811}, "Bưu cục Quận 5": {"address": "26 Nguyễn Thị, Q5", "lat": 10.7512, "lon": 106.6631}, "Bưu cục Quận 7": {"address": "1441 Huỳnh Tấn Phát, Q7", "lat": 10.7351, "lon": 106.7323}}
POPULAR_STOPS = {"120 cách mạng tháng tám": [10.7792, 106.6881], "240 điện biên phủ": [10.7865, 106.6915], "312 võ thị sáu": [10.7849, 106.6872], "02 võ oanh": [10.8021, 106.7142], "100 cao thắng": [10.7745, 106.6811], "320 nguyễn du": [10.7712, 106.6945], "hồ con rùa": [10.7827, 106.6961]}

# Khôi phục dữ liệu biểu đồ cột và miền
D_DATA = {"Thành công": [420, 380, 290, 180, 150], "Hoàn lại": [15, 22, 12, 8, 19]}
D_IDX = ["Quận 1", "Quận 3", "Quận 5", "Quận 7", "Quận 4"]
W_DATA = {"Xe máy": [2.1, 2.8, 3.2, 2.9, 3.5, 4.1, 1.5], "Xe tải": [8.5, 9.2, 11.0, 10.1, 12.4, 14.0, 5.0]}
W_IDX = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

if "map_ready" not in st.session_state: st.session_state.map_ready = False
if "lines_cache" not in st.session_state: st.session_state.lines_cache = []
if "text_cache" not in st.session_state: st.session_state.text_cache = []
if "steps_cache" not in st.session_state: st.session_state.steps_cache = []

# Quản lý trạng thái cập nhật đơn hàng thực tế lưu trong session_state
if "orders_db" not in st.session_state:
    st.session_state.orders_db = [
        {"Mã đơn": "VN94827HCM", "Người nhận": "Nguyễn Văn A", "Địa chỉ": "120 Cách Mạng Tháng Tám", "COD": "250.000đ", "Trạng thái": "🚚 Đang giao hàng"},
        {"Mã đơn": "VN10482HCM", "Người nhận": "Trần Thị B", "Địa chỉ": "240 Điện Biên Phủ", "COD": "0đ (Đã TT)", "Trạng thái": "🚚 Đang giao hàng"},
        {"Mã đơn": "VN88301HCM", "Người nhận": "Phạm Minh C", "Địa chỉ": "312 Võ Thị Sáu", "COD": "120.000đ", "Trạng thái": "✅ Giao thành công"},
        {"Mã đơn": "VN20491HCM", "Người nhận": "Lê Hoàng D", "Địa chỉ": "02 Võ Oanh", "COD": "540.000đ", "Trạng thái": "⏳ Chờ điều phối"}
    ]

with st.sidebar:
    st.write("### CẤU HÌNH PHÂN TUYẾN")
    selected_hub = st.selectbox("Chọn bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
