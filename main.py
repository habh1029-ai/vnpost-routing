import streamlit as st
import folium
from folium.plugins import Fullscreen
import math
import requests
import pandas as pd
from streamlit_folium import folium_static

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="VNPOST - Điều hành Logistics Đa điểm", layout="wide")

st.markdown("""
    <style>
        .main-title { font-size: 2rem !important; font-weight: 800; color: #0056b3; text-transform: uppercase; border-bottom: 4px solid #F2A900; padding-bottom: 10px; margin-bottom: 5px; }
        .metric-card { background: #f8fafc; border-left: 5px solid #F2A900; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 10px; }
        div.stButton > button:first-child { background: #F2A900; color: #003366 !important; font-weight: bold !important; border: none; border-radius: 6px; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# 2. CƠ SỞ DỮ LIỆU CỐ ĐỊNH
VNPOST_HUBS = {
    "Bưu cục Tân Định (Q1)": {"address": "230 Hai Bà Trưng, Quận 1", "lat": 10.7891, "lon": 106.6910},
    "Bưu cục Giao dịch Sài Gòn (Q1)": {"address": "2 Công xã Paris, Quận 1", "lat": 10.7798, "lon": 106.6999},
    "Bưu cục Quận 3": {"address": "2Bis Bà Huyện Thanh Quan, Quận 3", "lat": 10.7770, "lon": 106.6853},
    "Bưu cục Bàn Cờ (Q3)": {"address": "49A Cao Thắng, Quận 3", "lat": 10.7745, "lon": 106.6811},
    "Bưu cục Quận 5": {"address": "26 Nguyễn Thị, Quận 5", "lat": 10.7512, "lon": 106.6631},
    "Bưu cục Quận 7": {"address": "1441 Huỳnh Tấn Phát, Quận 7", "lat": 10.7351, "lon": 106.7323}
}

POPULAR_STOPS = {
    "100 cao thắng": [10.7745, 106.6811], "320 nguyễn du": [10.7712, 106.6945],
    "hồ con rùa": [10.7827, 106.6961], "220 hồ con rùa": [10.7827, 106.6961], "02 võ oanh": [10.8021, 106.7142]
}

DISTRICT_DATA = {"Thành công": [420, 380, 290, 180, 150], "Hoàn lại": [15, 22, 12, 8, 19]}
DISTRICT_INDEX = ["Quận 1", "Quận 3", "Quận 5", "Quận 7", "Quận 4"]
WEIGHT_DATA = {"Xe máy": [2.1, 2.8, 3.2, 2.9, 3.5, 4.1, 1.5], "Xe tải": [8.5, 9.2, 11.0, 10.1, 12.4, 14.0, 5.0]}
WEIGHT_INDEX = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

if "orders_df" not in st.session_state:
    st.session_state.orders_df = pd.DataFrame({
        "Mã Vận Đơn": ["VN94827HCM", "VN10482HCM", "VN58291HCM", "VN20481HCM", "VN39482HCM", "VN84920HCM", "VN74829HCM", "VN19482HCM", "VN63920HCM", "VN52910HCM", "VN48291HCM", "VN30291HCM", "VN91029HCM"],
        "Người Nhận": ["Nguyễn Văn A", "Trần Thị B", "Lê Hoàng C", "Phạm Minh D", "Hoàng Thục E", "Đỗ Tiến F", "Bùi Quang G", "Vũ Tuyết H", "Ngô Quốc I", "Lý Thanh J", "Dương Thúy K", "Tống Gia L", "Trịnh Đình M"],
        "Địa Chỉ Giao Hàng": ["100 Cao Thắng, Q3", "320 Nguyễn Du, Q1", "Hồ Con Rùa, Q3", "12 Lê Lợi, Q1", "45 Nguyễn Huệ, Q1", "88 Nam Kỳ Khởi Nghĩa, Q1", "150 Nguyễn Thị Minh Khai, Q3", "200 Cách Mạng Tháng 8, Q3", "15 Trần Hưng Đạo, Q5", "50 An Dương Vương, Q5", "300 Nguyễn Thị Thập, Q7", "55 Nguyễn Văn Linh, Q7", "105 Khánh Hội, Q4"],
        "Loại Hàng Hóa": ["Tài liệu mật", "Linh kiện điện tử", "Bưu kiện lớn", "Quần áo thời trang", "Mỹ phẩm cao cấp", "Giày dép thể thao", "Sách & Văn phòng phẩm", "Đồ gia dụng nhỏ", "Thực phẩm khô", "Trái cây nhập khẩu", "Thiết bị y tế", "Đồ chơi trẻ em", "Phụ kiện máy tính"],
        "Trạng Thái": ["Đang vận chuyển", "Đang vận chuyển", "Đang vận chuyển", "Chờ phân loại", "Chờ phân loại", "Đang vận chuyển", "Chờ phân loại", "Đang vận chuyển", "Chờ phân loại", "Chờ phân loại", "Đang vận chuyển", "Chờ phân loại", "Đang vận chuyển"]
    })

def get_coordinates_from_address(address_text):
    clean_addr = address_text.lower().strip()
    for key, coords in POPULAR_STOPS.items():
        if key in clean_addr: return {"lat": coords[0], "lon": coords[1]}
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(address_text + ', Ho Chi Minh, VN')}&format=json&limit=1"
        res = requests.get(url, headers={"User-Agent": "vnpost_bot_2026"}, timeout=5).json()
        if res: return {"lat": float(res[0]["lat"]), "lon": float(res[0]["lon"])}
    except: pass
    return {"lat": 10.7760 + (hash(address_text) % 100) / 5000, "lon": 106.7032 + (hash(address_text) % 100) / 5000}

# 3. THANH SIDEBAR
with st.sidebar:
    st.write("### CẤU HÌNH PHÂN TUYẾN")
    selected_start_hub = st.selectbox("Chọn bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
    st.text_area("Địa chỉ bưu cục điều phối:", value=VNPOST_HUBS[selected_start_hub]["address"], height=70, disabled=True)
    st.write("---")
    stops_input = st.text_area("Các điểm dừng phát hàng (1 dòng/địa chỉ):", value="100 Cao Thắng\n320 Nguyễn Du\nHồ Con Rùa\n02 Võ Oanh", height=120)
    vehicle_type = st.radio("Phương tiện vận chuyển:", ["Xe máy bưu tá chặng cuối", "Xe tải bưu chính lớn"])
    activated = st.button("TỐI ƯU LỘ TRÌNH THỰC ĐỊA")

# 4. GIAO DIỆN CHÍNH
st.markdown('<p class="main-title">VIETNAM POST - ĐIỀU HÀNH LOGISTICS ĐA ĐIỂM</p>', unsafe_allow_html=True)
tab_monitor, tab_map, tab_order = st.tabs(["Trung tâm Giám sát", "Tối ưu Tuyến đường Đa điểm", "Quản lý Vận đơn"])

with tab_monitor:
    st.write(f"**Đang giám sát:** {selected_start_hub}")
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.markdown('<div class="metric-card"><b>ĐA GIAO POD</b><h3 style="color:#0056b3;margin:0;">1.420 kiện</h3></div>', unsafe_allow_html=True)
    col_m2.markdown('<div class="metric-card"><b>BƯU TÁ THỰC ĐỊA</b><h3 style="color:#0056b3;margin:0;">45 Nhân sự</h3></div>', unsafe_allow_html=True)
    col_m3.markdown('<div class="metric-card"><b>TỶ LỆ TOÀN TRÌNH</b><h3 style="color:#e67e22;margin:0;">94.8 %</h3></div>', unsafe_allow_html=True)
    st.write("---")
    col_c1, col_c2 = st.columns(2)
    col_c1.write("#### Sản lượng giao thành công theo quận")
    col_c1.bar_chart(pd.DataFrame(DISTRICT_DATA, index=DISTRICT_INDEX), color=["#0056b3", "#ffc745"])
    col_c2.write("#### Trọng tải vận chuyển trong tuần (Tấn)")
    col_c2.area_chart(pd.DataFrame(WEIGHT_DATA, index=WEIGHT_INDEX), color=["#22c55e", "#ef4444"])

with tab_map:
    st.write("### Bản đồ điều phối chuỗi điểm giao hàng cho tài xế")
    col_left, col_right = st.columns([1.8, 1.2])
    start_lat, start_lon = VNPOST_HUBS[selected_start_hub]["lat"], VNPOST_HUBS[selected_start_hub]["lon"]
    
    m = folium.Map(location=[start_lat, start_lon], zoom_start=14)
