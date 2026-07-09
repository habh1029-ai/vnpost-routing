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

# CƠ SỞ DỮ LIỆU BƯU CỤC VNPOST TP.HCM (ĐÃ CHUẨN HÓA ĐỊA CHỈ ĐỂ TRA CỨU API)
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

# 3. THIẾT LẬP THANH SIDEBAR NGUYÊN BẢN CỦA BẠN
with st.sidebar:
    st.markdown("""### 🛠️ Cấu hình lộ trình""")
    selected_start_hub = st.selectbox("Chọn nhanh bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
    start_input = st.text_area("Từ bưu cục:", value=VNPOST_HUBS[selected_start_hub], height=70)
    end_input = st.text_input("Địa chỉ giao hàng nhận (Ví dụ: 100 Cao Thắng):", value="100 Cao Thắng")
    
    st.markdown("##### Phương tiện vận chuyển:")
    vehicle_type = st.radio(
        "Lựa chọn phương tiện:",
        ["🛵 Xe máy bưu tá chặng cuối", "🚚 Xe tải bưu chính lớn"],
        label_visibility="collapsed"
    )
    
    activated = st.button("🚀 TÍNH TOÁN LỘ TRÌNH THỰC ĐỊA")

# BANNER TIÊU ĐỀ CHÍNH TRÊN CÙNG TRANG WEB
st.markdown("""<p class="main-title">✉️ HỆ THỐNG ĐIỀU HÀNH BƯU CHÍNH THÔNG MINH VIETNAM POST</p>""", unsafe_allow_html=True)
st.markdown("""*Trực quan hóa mạng lưới Logistics, Định tuyến chặng cuối & Giám sát trạng thái thời gian thực*""")

# KHỞI TẠO CÁC TAB CHỨC NĂNG CHÍNH
tab_enterprise, tab_routing, tab_status = st.tabs([
    "📊 Trung tâm Giám sát", 
    "🗺️ Tối ưu Tuyến đường", 
    "📦 Quản lý Vận đơn"
])

# ------------------------------------------
# TAB 1: TRUNG TÂM GIÁM SÁT
# ------------------------------------------
with tab_enterprise:
    st.markdown("""### 📊 Tổng quan Hoạt động Mạng lưới""")
    st.markdown(f"<div style='background-color:#e0f2fe; padding:12px; border-radius:8px; border-left:4px solid #0284c7; color:#0369a1;'>📍 <b>Bưu cục đang giám sát:</b> {selected_start_hub} — <b>Địa chỉ:</b> {VNPOST_HUBS[selected_start_hub]}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    col_info1, col_info2 = st.columns([1, 1])
    with col_info1:
        st.markdown("""#### ⚡ Hiệu suất khai thác trong ngày""")
        st.write("Tỷ lệ bưu phẩm hoàn thành chặng cuối:")
        st.progress(0.85)
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("""<div class="metric-card"><p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:bold;">ĐÃ GIAO THÀNH CÔNG</p><h2 style="margin:5px 0 0 0; color:#0056b3; font-weight:800;">1,420 kiện</h2><p style="margin:0; font-size:0.85rem; color:#16a34a;">↗️ +12% so với hôm qua</p></div>""", unsafe_allow_html=True)
        with col_m2:
            st.markdown("""<div class="metric-card"><p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:bold;">BƯU TÁ THỰC ĐỊA</p><h2 style="margin:5px 0 0 0; color:#0056b3; font-weight:800;">45 Nhân sự</h2><p style="margin:0; font-size:0.85rem; color:#0284c7;">🔵 Trạng thái: Sẵn sàng</p></div>""", unsafe_allow_html=True)
    
    with col_info2:
        with st.container(border=True):
            st.markdown("""🎯 **Quản lý Tải trọng & Khuyến cáo Phân tuyến**""")
            st.warning("⚠️ Hệ thống phát hiện có **24 bưu phẩm cồng kềnh** có kích thước vượt giỏ hàng xe máy thông thường.")
            st.markdown("""
            * 🛵 **Xe máy bưu tá:** Phù hợp bưu phẩm thư từ, tài liệu gọn (< 5kg).
            * 🚚 **Xe tải bưu chính nhỏ (1.25 Tấn):** Đã phân bổ 2 xe hỗ trợ đi gom tại các tuyến đường trục lớn để bảo đảm an toàn hàng hóa.
            """)

# ------------------------------------------
# TAB 2: TỐI ƯU TUYẾN ĐƯỜNG (BẢN ĐỒ)
# ------------------------------------------
with tab_routing:
    st.markdown("""### 🗺️ Bản đồ Định tuyến & Tối ưu lộ trình bưu tá""")
    
    col_left, col_right = st.columns([1.8, 1.2])
    
    # KHỞI TẠO BẢN ĐỒ AN TOÀN TRƯỚC (SỬA TRIỆT ĐỂ LỖI NAMERROR BIẾN M)
    default_lat, default_lon = 10.7760, 106.7032
    m = folium.Map(location=[default_lat, default_lon], zoom_start=14, control_scale=True)

    if activated:
        if not start_input.strip() or not end_input.strip():
            with col_left:
                st.warning("⚠️ Vui lòng điền đầy đủ thông tin vị trí ở thanh Sidebar bên trái!")
                folium_static(m, width=700, height=480)
        else:
            try:
                with st.spinner("🔍 Đang kết nối máy chủ dữ liệu nền vệ tinh GPS..."):
                    loc1 = get_coordinates_from_address(start_input)
                    loc2 = get_coordinates_from_address(end_input)
                    
                    if not loc1:
                        with col_left:
                            st.error(f"❌ Không tìm thấy vị trí bưu cục: '{start_input}'")
                            folium_static(m, width=700, height=480)
                    elif not loc2:
                        with col_left:
                            st.error(f"❌ Không tìm thấy vị trí địa chỉ khách hàng: '{end_input}'")
                            folium_static(m, width=700, height=480)
                    else:
                        url = f"http://router.project-osrm.org/route/v1/driving/{loc
