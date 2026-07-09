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

# 3. CƠ SỞ DỮ LIỆU BƯU CỤC VNPOST TP.HCM
VNPOST_HUBS = {
    "Bưu cục Tân Định (Q1)": "230 Hai Bà Trưng, Quận 1",
    "Bưu cục Giao dịch Sài Gòn (Q1)": "2 Công xã Paris, Quận 1",
    "Bưu cục Quận 3": "2Bis Bà Huyện Thanh Quan, Quận 3",
    "Bưu cục Bàn Cờ (Q3)": "49A Cao Thắng, Quận 3",
    "Bưu cục Quận 5": "26 Nguyễn Thị, Quận 5",
    "Bưu cục Quận 7": "1441 Huỳnh Tấn Phát, Quận 7"
}

# 4. DỮ LIỆU THỐNG KÊ BIỂU ĐỒ (MOCK DATA)
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

# BỔ SUNG THÊM 10 KIỆN HÀNG MỚI (TỔNG CỘNG 13 VẬN ĐƠN)
MOCK_ORDERS = {
    "Mã Vận Đơn": [
        "VN94827HCM", "VN10482HCM", "VN58291HCM", "VN20481HCM", "VN39482HCM",
        "VN84920HCM", "VN74829HCM", "VN19482HCM", "VN63920HCM", "VN52910HCM",
        "VN48291HCM", "VN30291HCM", "VN91029HCM"
    ],
    "Người Nhận": [
        "Nguyễn Văn A", "Trần Thị B", "Lê Hoàng C", "Phạm Minh D", "Hoàng Thục E",
        "Đỗ Tiến F", "Bùi Quang G", "Vũ Tuyết H", "Ngô Quốc I", "Lý Thanh J",
        "Dương Thúy K", "Tống Gia L", "Trịnh Đình M"
    ],
    "Địa Chỉ Giao Hàng": [
        "100 Cao Thắng, Q3", "320 Nguyễn Du, Q1", "Hồ Con Rùa, Q3", "12 Lê Lợi, Q1", "45 Nguyễn Huệ, Q1",
        "88 Nam Kỳ Khởi Nghĩa, Q1", "150 Nguyễn Thị Minh Khai, Q3", "200 Cách Mạng Tháng 8, Q3", "15 Trần Hưng Đạo, Q5", "50 An Dương Vương, Q5",
        "300 Nguyễn Thị Thập, Q7", "55 Nguyễn Văn Linh, Q7", "105 Khánh Hội, Q4"
    ],
    "Loại Hàng Hóa": [
        "Tài liệu mật", "Linh kiện điện tử", "Bưu kiện lớn", "Quần áo thời trang", "Mỹ phẩm cao cấp",
        "Giày dép thể thao", "Sách & Văn phòng phẩm", "Đồ gia dụng nhỏ", "Thực phẩm khô", "Trái cây nhập khẩu",
        "Thiết bị y tế", "Đồ chơi trẻ em", "Phụ kiện máy tính"
    ],
    "Trạng Thái": [
        "Đang vận chuyển", "Đang vận chuyển", "Đang vận chuyển", "Chờ phân loại", "Chờ phân loại",
        "Đang vận chuyển", "Chờ phân loại", "Đang vận chuyển", "Chờ phân loại", "Chờ phân loại",
        "Đang vận chuyển", "Chờ phân loại", "Đang vận chuyển"
    ]
}

# Hàm định vị lấy tọa độ từ địa chỉ chuỗi thông qua Nominatim OpenStreetMap API
def get_coordinates_from_address(address_text):
    try:
        full_query = f"{address_text}, Ho Chi Minh City, Vietnam"
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(full_query)}&format=json&limit=1"
        headers = {"User-Agent": "vietnam_post_routing_app_2026"}
        response = requests.get(url, headers=headers, timeout=10).json()
        if response:
            return {
                "lat": float(response[0]["lat"]), 
                "lon": float(response[0]["lon"])
            }
        return None
    except Exception:
        return None

# 5. THANH SIDEBAR ĐIỀU HƯỚNG VÀ THIẾT LẬP LỘ TRÌNH
with st.sidebar:
    st.write("### CẤU HÌNH PHÂN TUYẾN")
    selected_start_hub = st.selectbox("Chọn bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
    start_input = st.text_area("Địa chỉ bưu cục điều phối:", value=VNPOST_HUBS[selected_start_hub], height=70)
    
    st.write("---")
    st.write("Danh sách các điểm giao hàng (Multi-drop):")
    st.caption("Nhập mỗi địa chỉ giao nhận trên 1 dòng tách biệt:")
    
    default_stops = "100 Cao Thắng, Quận 3\n320 Nguyễn Du, Quận 1\nHồ Con Rùa, Quận 3"
    stops_input = st.text_area("Các điểm dừng phát hàng:", value=default_stops, height=120)
    
    vehicle_type = st.radio("Phương tiện vận chuyển:", ["Xe máy bưu tá chặng cuối", "Xe tải bưu chính lớn"])
    activated = st.button("TỐI ƯU HÓA LỘ TRÌNH THỰC ĐỊA")

# 6. HIỂN THỊ TIÊU ĐỀ TRANG CHÍNH TIẾNG VIỆT CÓ DẤU
st.markdown('<p class="main-title">VIETNAM POST - ĐIỀU HÀNH LOGISTICS ĐA ĐIỂM</p>', unsafe_allow_html=True)
st.write("*Hệ thống trực quan hóa mạng lưới điều phối, định tuyến chuỗi điểm dừng chặng cuối real-time*")

tab_monitor, tab_map, tab_order = st.tabs([
    "Trung tâm Giám sát", 
    "Tối ưu Tuyến đường Đa điểm", 
    "Quản lý Vận đơn"
])

# ------------------------------------------
# TAB 1: TRUNG TÂM GIÁM SÁT THỐNG KÊ
# ------------------------------------------
with tab_monitor:
    st.write(f"**Đang giám sát:** {selected_start_hub}")
    col_m1, col_m2, col_m3 = st.
