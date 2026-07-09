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
    initial_sidebar_state="expanded"
)

# 2. CHÈN CSS CUSTOM ĐỂ TRANG TRÍ WEB SINH ĐỘNG (NHẬN DIỆN VNPOST)
st.markdown("""
    <style>
        /* Đổi màu nền thanh sidebar bên trái */
        [data-testid="stSidebar"] {
            background-color: #fcf8f2;
            border-right: 2px solid #F2A900;
        }
        
        /* Định dạng lại tiêu đề chính sinh động hơn */
        .main-title {
            font-size: 2.3rem !important;
            font-weight: 800;
            color: #0056b3;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
            border-bottom: 4px solid #F2A900;
            padding-bottom: 10px;
        }
        
        /* Tạo khối Card chỉ số lấp lánh, bo góc nghệ thuật */
        .metric-card {
            background: linear-gradient(145deg, #ffffff, #f1f5f9);
            border-left: 5px solid #F2A900;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(242, 169, 0, 0.15);
        }
        
        /* Làm đẹp cho các Tab điều hướng */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #f1f5f9;
            border-radius: 8px 8px 0px 0px;
            padding: 10px 20px;
            font-weight: bold;
            color: #475569;
        }
        .stTabs [aria-selected="true"] {
            background-color: #0056b3 !important;
            color: white !important;
            border-bottom: 3px solid #F2A900 !important;
        }
        
        /* Tùy chỉnh nút bấm chính */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #F2A900, #ffc745);
            color: #003366 !important;
            font-weight: bold !important;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            box-shadow: 0 4px 10px rgba(242,169,0,0.3);
            width: 100%;
            transition: all 0.3s;
        }
        div.stButton > button:first-child:hover {
            background: linear-gradient(135deg, #0056b3, #0076f7);
            color: white !important;
            box-shadow: 0 4px 10px rgba(0,86,179,0.3);
        }
    </style>
""", unsafe_allow_html=True)

# CƠ SỞ DỮ LIỆU BƯU CỤC VNPOST TP.HCM ĐÃ ĐƯỢC LÀM SẠCH CHỮ QUẬN TRONG NGOẶC KÉP
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
    "Bưu cục Quận 7": "1441 Huỳnh Tấn Phát, Quận 7",
    "Bưu cục Chánh Hưng": "Chung cư Phạm Thế Hiển, Quận 8",
    "Bưu cục Quận 8": "428 Tùng Thiện Vương, Quận 8",
    "Bưu cục Quận 10": "157 Lý Thái Tổ, Quận 10",
    "Bưu cục Hoà Hưng": "411 Cách Mạng Tháng Tám, Quận 10",
    "Bưu cục Phú Thọ": "270 Lý Thường Kiệt, Quận 10",
    "Bưu cục Quận 11": "244 Minh Phụng, Quận 11",
    "Bưu cục Quang Trung": "Tô Ký, Đông Hưng Thuận, Quận 12",
    "Bưu cục Tân Thới Nhất": "44 Phan Văn Hớn, Quận 12",
    "Bưu cục An Khánh": "D7 Trần Não, Quận 2",
    "Bưu cục Bình Trưng": "42 Nguyễn Duy Trinh, Quận 2",
    "Bưu cục Chợ Nhỏ": "95 Man Thiện, Quận 9",
    "Bưu cục Phước Bình": "45 Đại lộ 2, Quận 9",
    "Bưu cục Bình Triệu": "705 Gò Dưa, Thủ Đức",
    "Bưu cục Linh Trung": "16 Đường số 4, Thủ Đức",
    "Bưu cục Thủ Đức": "128A Kha Vạn Cân, Thủ Đức",
    "Bưu cục Thị Nghè": "23 Xô Viết Nghệ Tĩnh, Bình Thạnh",
    "Bưu cục Bình Thạnh": "3 Phan Đăng Lưu, Bình Thạnh",
    "Bưu cục Phú Nhuận": "241 Phan Đình Phùng, Phú Nhuận",
    "Bưu cục Gò Vấp": "555 Lê Quang Định, Gò Vấp",
    "Bưu cục Lê Văn Thọ": "56 Cây Trâm, Gò Vấp",
    "Bưu cục Tân Sơn Nhất": "2B Bạch Đằng, Tân Bình",
    "Bưu cục Tân Bình": "288 Hoàng Văn Thụ, Tân Bình",
    "Bưu cục Chí Hòa": "695 Cách Mạng Tháng Tám, Tân Bình",
    "Bưu cục Gò Dầu": "Chung cư Gò Dầu 2, Tân Phú",
    "Bưu cục Tân Phú": "90 Nguyễn Sơn, Tân Phú",
    "Bưu cục Bình Hưng Hòa": "1026 Tân Kỳ Tân Quý, Bình Tân",
    "Bưu cục Bưu Điện Trung Tâm Hóc Môn": "57 Lý Nam Đế, Hóc Môn",
    "Bưu cục Tân Phú Trung": "912 Quốc Lộ 22, Củ Chi",
    "Bưu cục Bình Chánh": "E9 Nguyễn Hữu Trí, Bình Chánh"
}

# ALGORITHM: GEOCODING TO GPS
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

# ALGORITHM: TURN BY TURN NAVIGATION
def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lon = lon2_rad - lon1_rad
    x = math.sin(d_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - (math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(d_lon))
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    return (initial_bearing + 360) % 360

def generate_turn_by_turn(geometry_coords):
    if len(geometry_coords) < 3:
        return ["🟢 Xuất phát: Di chuyển thẳng theo lộ trình."]
    instructions = []
    instructions.append("🟢 **Xuất phát:** Khởi hành từ bưu cục, bám sát lòng đường hiện tại.")
    sample_rate = max(1, len(geometry_coords) // 6)
    for i in range(sample_rate, len(geometry_coords) - sample_rate, sample_rate):
        p1 = geometry_coords[i - sample_rate]
        p2 = geometry_coords[i]
        p3 = geometry_coords[i + sample_rate]
        b1 = calculate_bearing(p1[0], p1[1], p2[0], p2[1])
        b2 = calculate_bearing(p2[0], p2[1], p3[0], p3[1])
        turn = (b2 - b1 + 360) % 360
        if 25 <= turn < 155:
            instructions.append("↩️ **Rẽ phải** tại giao lộ phía trước theo hành trình.")
        elif 205 <= turn < 335:
            instructions.append("↪️ **Rẽ trái** vào tuyến đường phân phối chặng cuối.")
    instructions.append("🔴 **Đến nơi:** Địa điểm bàn giao hàng nằm ngay trước hướng di chuyển.")
    return instructions[:6]


# ==========================================
# GIAO DIỆN THANH TABS HIỆN ĐẠI
# ==========================================
tab_enterprise, tab_routing, tab_status = st.tabs([
    "🏢 Trung tâm Giám sát", 
    "🗺️ Tối ưu Tuyến đường", 
    "📦 Quản lý Vận đơn"
])

# ------------------------------------------
# MỤC 1: TRUNG TÂM GIÁM SÁT DOANH NGHIỆP
# ------------------------------------------
with tab_enterprise:
    st.markdown("### 📊 Tổng quan Hoạt động Mạng lưới Bưu chính")
    
    col_sel1, col_sel2 = st.columns([1, 1])
    with col_sel1:
        hub_selected = st.selectbox("Lựa chọn bưu cục quản lý hệ thống dữ liệu:", list(VNPOST_HUBS.keys()))
    with col_sel2:
        st.markdown(f"<div style='margin-top:32px; background-color:#e0f2fe; padding:10px; border-radius:8px; border-left:4px solid #0284c7; color:#0369a1;'>📍 <b>Địa chỉ phục vụ:</b> {VNPOST_HUBS[hub_selected]}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_info1, col_info2 = st.columns([1, 1])
    with col_info1:
        st.markdown("#### ⚡ Hiệu suất khai thác trong ngày")
        st.write("Tỷ lệ bưu phẩm hoàn thành chặng cuối:")
        st.progress(0.85)
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(f"""
                <div class="metric-card">
                    <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:bold;">ĐÃ GIAO THÀNH CÔNG</p>
                    <h2 style="margin:5px 0 0 0; color:#0056b3; font-weight:800;">1,420 kiện</h2>
                    <p style="margin:0; font-size:0.85rem; color:#16a34a;">↗️ +12% so với hôm qua</p>
                </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
                <div class="metric-card">
                    <p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:bold;">BƯU TÁ THỰC ĐỊA</p>
                    <h2 style="margin:5px 0 0 0; color:#0056b3; font-weight:800;">45 Nhân sự</h2>
                    <p style="margin:0; font-size:0.85rem; color:#0284c7;">🔵 Trạng thái: Sẵn sàng</p>
                </div>
            """, unsafe_allow_html=True)
        
    with col_info2:
        with st.container(border=True):
            st.markdown("🎯 **Quản lý Tải trọng & Khuyến cáo Phân tuyến**")
            st.warning("⚠️ Hệ thống phát hiện có **24 bưu phẩm cồng kềnh** có kích thước vượt giỏ hàng xe máy thông thường.")
            st.markdown("""
            * 🛵 **Xe máy bưu tá:** Phù hợp bưu phẩm thư từ, tài liệu gọn (< 5kg).
            * 🚚 **Xe tải bưu chính nhỏ (1.25 Tấn):** Đã phân bổ 2 xe hỗ trợ đi gom tại các tuyến đường trục lớn để bảo đảm an toàn hàng hóa.
            """)

# ------------------------------------------
# MỤC 2: TỐI ƯU TUYẾN ĐƯỜNG (MAP & CHỈ ĐƯỜNG)
# ------------------------------------------
with tab_routing:
    st.markdown("### 🗺️ Bản đồ Định tuyến & Tối ưu lộ trình bưu tá")
    
    st.sidebar.markdown("<h3 style='color:#0056b3;'>⚡ Thiết lập Lộ trình Tối ưu</h3>", unsafe_allow_html=True)
    
    selected_start_hub = st.sidebar.selectbox("Chọn nhanh bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
    start_address = VNPOST_HUBS[selected_start_hub]
    
    start_input = st.sidebar.text_area("Từ địa chỉ bưu cục:", value=start_address, height=70)
    end_input = st.sidebar.text_input("Địa chỉ giao hàng khách nhận:", "100 Cao Thắng")
    vehicle_type = st.sidebar.radio("Phương tiện vận chuyển:", ["🛵 Xe máy bưu tá chặng cuối", "🚚 Xe tải bưu chính lớn"])
    
    st.sidebar.markdown("---")
    activated = st.sidebar.button("🚀 TÍNH TOÁN LỘ TRÌNH THỰC ĐỊA")

    col_left, col_right = st.columns([2, 1])

    default_lat, default_lon = 10.7760, 106.7032
    m = folium.Map(location=[default_lat, default_lon], zoom_start=14, control_scale=True)
    folium.TileLayer('openstreetmap', name='Bản đồ đường phố').add_to(m)

    if activated:
        if not start_input.strip() or not end_input.strip():
            st.sidebar.warning("⚠️ Vui lòng không để trống địa chỉ!")
        elif start_input.strip().lower() == end_input.strip().lower():
            st.sidebar.warning("⚠️ Điểm xuất phát và đích đến trùng nhau!")
        else:
            try:
                with st.spinner("🔍 Đang kết nối OSRM định vị..."):
                    loc1 = get_coordinates_from_address(start_input)
                    loc2 = get_coordinates_from_address(end_input)
                    
                    if not loc1:
                        st.error(f"❌ Bản đồ chưa nhận diện được bưu cục: '{start_input}'.")
                    elif not loc2:
                        st.error(f"❌ Không tìm thấy vị trí khách hàng: '{end_input}'")
                    else:
                        profile = "driving"
                        # ĐÃ SỬA: Sửa dấu gạch chéo sang dấu phẩy giữa lon và lat của loc1
                        url = f"http://router.project-osrm.org/route/v1/{profile}/{loc1['lon']},{loc1['lat']};{loc2['lon']},{loc2['lat']}?overview=full&geometries=geojson"
                        response = requests.get(url).json()
                        
                        if response.get('code') == 'Ok':
                            route_data = response['routes'][0]
                            geometry = route_data['geometry']['coordinates']
                            detailed_route_gps = [[coord[1], coord[0]] for coord in geometry]
                            
                            total_distance = route_data['distance']
                            duration = route_data['duration']
                            distance_km = total_distance / 1000
                            
                            if "🛵" in vehicle_type:
                                fuel_consumption = (distance_km / 100) * 2.5 * 23000
                            else:
                                fuel_consumption = (distance_km / 100) * 9.0 * 23000
                            
                            nav_instructions = generate_turn_by_turn(detailed_route_gps)
                            
                            center_lat = (loc1['lat'] + loc2['lat']) / 2
                            center_lon = (loc1['lon'] + loc2['lon']) / 2
                            m = folium.Map(location=[center_lat, center_lon], zoom_start=15, control_scale=True)
                            folium.TileLayer('openstreetmap').add_to(m)
                            
                            folium.Marker([loc1['lat'], loc1['lon']], tooltip=f"Bưu cục: {loc1['display_name']}", icon=folium.Icon(color='green', icon='play')).add_to(m)
                            folium.Marker([loc2['lat'], loc2['lon']], tooltip=f"Khách hàng: {loc2['display_name']}", icon=folium.Icon(color='red', icon='flag')).add_to(m)
                            folium.PolyLine(detailed_route_gps, color="#0056b3", weight=6, opacity=0.85).add_to(m)
                            
                            with col_left:
                                st.markdown("<div style='background-color:#dcfce7; padding:10px; border-radius:8px; color:#15803d; font-weight:bold; margin-bottom:10px;'>✅ ĐÃ TỐI ƯU TUYẾN ĐƯỜNG BÁM LÒNG ĐƯỜNG</div>", unsafe_allow_html=True)
                                folium_static(m, width=800, height=520)
                                
                            with col_right:
                                st.markdown("#### 📱 Thiết bị bưu tá")
                                with st.container(border=True):
                                    st.markdown(f"🛣️ **Khoảng cách:** `{distance_km:.2f} km`")
                                    st.markdown(f"⏱️ **Thời gian di chuyển:** `{duration/60:.1f} phút`")
                                    st.markdown(f"💰 **Trợ cấp xăng xe:** `{fuel_consumption:.0f} VNĐ`")
                                    st.markdown("---")
                                    st.write("🧭 **Chỉ dẫn thực địa:**")
                                    for inst in nav_instructions:
                                        st.write(inst)
                        else:
                            st.error("❌ Máy chủ định tuyến lỗi dữ liệu tuyến đường.")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
    else:
        with col_left:
            folium_static(m, width=800, height=520)
        with col_right:
            st.info("💡 Điền thông tin hành trình và click 'Tính toán lộ trình thực địa' ở thanh bên trái để xem kết quả trực quan.")

# ------------------------------------------
# MỤC 3: QUẢN LÝ TRẠNG THÁI VẬN ĐƠN POD
# ------------------------------------------
with tab_status:
    st.markdown("### 📦 Quản lý Trạng thái Vận đơn Chặng cuối")
    
    mock_orders = {
        "Mã Vận Đơn": ["VN94827HCM", "VN10482HCM", "VN58291HCM", "VN30294HCM"],
        "Người Nhận": ["Nguyễn Văn A", "Trần Thị B", "Lê Hoàng C", "Phạm Minh D"],
        "Địa Chỉ": ["100 Cao Thắng, Q3", "320 Nguyễn Du, Q1", "Hồ Con Rùa, Q3", "Vòng xoay Dân Chủ"],
        "Loại Hàng": ["Tài liệu mật", "Linh kiện điện tử", "Bưu kiện lớn", "Hàng dễ vỡ"]
    }
    df_orders = pd.DataFrame(mock_orders)
    st.dataframe(df_orders, use_container_width=True)
    
    st.markdown("---")
    
    col_status1, col_status2 = st.columns([1, 1])
    with col_status1:
        st.markdown("#### 🆔 Cập nhật tiến độ giao hàng")
        selected_order = st.selectbox("Chọn mã vận đơn cần cập nhật:", df_orders["Mã Vận Đơn"])
        
        status_options = [
            "🛵 Bưu tá đang đi phát hàng chặng cuối",
            "✅ Phát thành công (Đã ký nhận POD)",
            "❌ Giao hàng thất bại / Khách hẹn lại",
            "🚨 Báo cáo sự cố khẩn cấp trên đường (SOS)"
        ]
        current_status = st.selectbox("Trạng thái mới:", status_options, index=0)
        
        if "Thất bại" in current_status:
            st.selectbox("Lý do chi tiết:", ["Khách tắt máy không liên lạc được", "Khách hẹn đổi ca", "Sai thông tin số nhà"])
        elif "Thành công" in current_status:
            st.file_uploader("📸 Tải lên ảnh chụp ký nhận thực tế tại nhà khách (Bằng chứng POD):", type=["jpg", "png", "jpeg"])
        elif "SOS" in current_status:
            st.error("🚨 HỆ THỐNG CẢNH BÁO SỰ CỐ KHẨN CẤP")
            st.text_area("Mô tả sự cố:", "Hỏng lốp xe, cần cứu hộ.")
            
        note = st.text_area("Ghi chú bổ sung:", "Đang di chuyển.")
        if st.button("💾 ĐỒNG BỘ LÊN TỔNG ĐÀI VNPOST"):
            st.toast("Đồng bộ thành công!", icon="🚀")
            
    with col_status2:
        st.markdown("#### 🕒 Nhật ký hành trình (Timeline)")
        with st.container(border=True):
            st.markdown(f"**Vận đơn:** `{selected_order}`")
            st.markdown(f"📍 **Trạng thái hiện tại:** `{current_status}`")
            st.markdown("---")
            st.markdown(f"- **[2026-07-09 09:35]** {current_status} | *{note}*")
            st.markdown("- **[2026-07-09 06:15]** 📥 Đã nhập kho bưu cục chặng cuối.")
            st.markdown("- **[2026-07-08 14:20]** 🚚 Đang vận chuyển trục bưu chính quốc gia.")
