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

# CƠ SỞ DỮ LIỆU BƯU CỤC VNPOST TP.HCM
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

# TAB 1: GIÁM SÁT ĐƠN VỊ
with tab_enterprise:
    st.markdown("### 📊 Tổng quan Hoạt động Mạng lưới")
    hub_selected = st.selectbox("Lựa chọn bưu cục dữ liệu:", list(VNPOST_HUBS.keys()))
    st.markdown(f"<div style='background-color:#e0f2fe; padding:12px; border-radius:8px; border-left:4px solid #0284c7; color:#0369a1;'>📍 <b>Địa chỉ:</b> {VNPOST_HUBS[hub_selected]}</div>", unsafe_allow_html=True)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown('<div class="metric-card"><b>ĐÃ GIAO THÀNH CÔNG</b><h2>1,420 kiện</h2><p style="color:#16a34a;">↗️ +12% hôm nay</p></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown('<div class="metric-card"><b>BƯU TÁ THỰC ĐỊA</b><h2>45 Nhân sự</h2><p style="color:#0284c7;">🔵 Sẵn sàng kết nối</p></div>', unsafe_allow_html=True)

# TAB 2: TỐI ƯU TUYẾN ĐƯỜNG (THIẾT KẾ ĐÁP ỨNG DI ĐỘNG TUYỆT ĐỐI)
with tab_routing:
    st.markdown("### 🗺️ Định tuyến Di động thông minh")
    
    # ĐƯA PHẦN THIẾT LẬP VÀO KHUNG CHÍNH (BƯU TÁ DÙNG ĐIỆN THOẠI KHÔNG BỊ KHUẤT)
    with st.container(border=True):
        st.markdown("##### ⚡ Thiết lập Lộ trình Chặng cuối")
        col_input1, col_input2 = st.columns([1, 1])
        with col_input1:
            selected_start_hub = st.selectbox("1. Chọn nhanh bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
            start_input = st.text_input("Vị trí bưu cục phát:", value=VNPOST_HUBS[selected_start_hub])
        with col_input2:
            end_input = st.text_input("2. Nhập địa chỉ khách hàng nhận:", "100 Cao Thắng")
            vehicle_type = st.radio("Phương tiện:", ["🛵 Xe máy bưu tá chặng cuối", "🚚 Xe tải bưu chính"], horizontal=True)
        
        activated = st.button("🚀 BẮT ĐẦU TÍNH TOÁN LỘ TRÌNH THỰC ĐỊA")

    st.markdown("---")
    col_left, col_right = st.columns([1.8, 1.2])

    default_lat, default_lon = 10.7760, 106.7032
    m = folium.Map(location=[default_lat, default_lon], zoom_start=14, control_scale=True)

    if activated:
        if not start_input.strip() or not end_input.strip():
            st.warning("⚠️ Vui lòng điền đầy đủ thông tin vị trí!")
        else:
            try:
                with st.spinner("🔍 Đang đồng bộ tọa độ vệ tinh GPS..."):
                    loc1 = get_coordinates_from_address(start_input)
                    loc2 = get_coordinates_from_address(end_input)
                    
                    if not loc1: st.error(f"❌ Không tìm thấy vị trí bưu cục: '{start_input}'")
                    elif not loc2: st.error(f"❌ Không tìm thấy vị trí khách hàng: '{end_input}'")
                    else:
                        url = f"http://router.project-osrm.org/route/v1/driving/{loc1['lon']},{loc1['lat']};{loc2['lon']},{loc2['lat']}?overview=full&geometries=geojson"
                        response = requests.get(url).json()
                        
                        if response.get('code') == 'Ok':
                            route_data = response['routes'][0]
                            detailed_route_gps = [[c[1], c[0]] for c in route_data['geometry']['coordinates']]
                            distance_km = route_data['distance'] / 1000
                            duration_min = route_data['duration'] / 60
                            fuel = (distance_km / 100) * (2.5 if "🛵" in vehicle_type else 9.0) * 23000
                            
                            # Cập nhật bản đồ
                            m = folium.Map(location=[(loc1['lat']+loc2['lat'])/2, (loc1['lon']+loc2['lon'])/2], zoom_start=15)
                            folium.Marker([loc1['lat'], loc1['lon']], tooltip="Bưu cục", icon=folium.Icon(color='green', icon='play')).add_to(m)
                            folium.Marker([loc2['lat'], loc2['lon']], tooltip="Khách hàng", icon=folium.Icon(color='red', icon='flag')).add_to(m)
                            folium.PolyLine(detailed_route_gps, color="#0056b3", weight=6).add_to(m)
                            
                            with col_left:
                                st.markdown("<div style='color:#15803d; font-weight:bold; margin-bottom:5px;'>✅ ĐÃ TỐI ƯU TUYẾN ĐƯỜNG</div>", unsafe_allow_html=True)
                                folium_static(m, width=700, height=480)
                            with col_right:
                                st.markdown("##### 📱 Kết quả điều hành")
                                with st.container(border=True):
                                    st.write(f"🛣️ **Quãng đường:** `{distance_km:.2f} km`")
                                    st.write(f"⏱️ **Thời gian dự kiến:** `{duration_min:.1f} phút`")
                                    st.write(f"💰 **Trợ cấp nhiên liệu:** `{fuel:.0f} VNĐ`")
                                    st.markdown("---")
                                    for inst in generate_turn_by_turn(detailed_route_gps):
                                        st.write(inst)
                        else: st.error("❌ Lỗi kết nối dữ liệu máy chủ mạng lưới.")
            except Exception as e: st.error(f"❌ Sự cố kết nối: {e}")
    else:
        with col_left: folium_static(m, width=700, height=480)
        with col_right: st.info("💡 Nhấn nút tính toán để cập nhật dữ liệu bản đồ thời gian thực.")

# TAB 3: TRẠNG THÁI VẬN ĐƠN
with tab_status:
    st.markdown("### 📦 Quản lý Trạng thái Vận đơn Chặng cuối")
    df_orders = pd.DataFrame({
        "Mã Vận Đơn": ["VN94827HCM", "VN10482HCM"],
        "Người Nhận": ["Nguyễn Văn A", "Trần Thị B"],
        "Địa Chỉ": ["100 Cao Thắng, Q3", "320 Nguyễn Du, Q1"]
    })
    st.dataframe(df_orders, use_container_width=True)
