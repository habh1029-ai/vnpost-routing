import streamlit as st
import folium
import math
import requests
import pandas as pd

# 1. CẤU HÌNH GIAO DIỆN WEB TOÀN MÀN HÌNH
st.set_page_config(page_title="Hệ thống Điều hành Bưu chính Vietnam Post", layout="wide")

def get_advanced_libraries():
    from streamlit_folium import folium_static
    from folium.plugins import Fullscreen
    return folium_static, Fullscreen

# TIÊU ĐỀ ĐIỀU HÀNH CHÍNH THEO NHẬN DIỆN THƯƠNG HIỆU VNPOST
st.title("✉️ TỐI ƯU HÓA TUYẾN ĐƯỜNG TRONG HOẠT ĐỘNG BƯU CHÍNH CỦA VIETNAM POST")
st.subheader("Hệ thống quản lý, điều phối trạng thái và định tuyến thực địa thông minh")

# CƠ SỞ DỮ LIỆU BƯU CỤC VNPOST TP.HCM CHUẨN
VNPOST_HUBS = {
    "Bưu cục Giao dịch Sài Gòn (Q1)": "2 Công xã Paris, Phường Bến Nghé, Quận 1",
    "Bưu cục Giao Dịch Quốc Tế Sài Gòn (Q1)": "117-119 Hai Bà Trưng, Phường Bến Nghé, Quận 1",
    "Bưu cục Tân Định (Q1)": "230 Hai Bà Trưng, Phường Tân Định, Quận 1",
    "Bưu cục Trần Hưng Đạo (Q1)": "447B Trần Hưng Đạo, Phường Cầu Kho, Quận 1",
    "Bưu cục Quận 3": "2Bis Bà Huyện Thanh Quan, Phường 6, Quận 3",
    "Bưu cục Bàn Cờ (Q3)": "49A Cao Thắng, Phường 3, Quận 3",
    "Bưu cục Vườn Xoài (Q3)": "472 Lê Văn Sỹ, Phường 14, Quận 3",
    "Bưu cục Quận 4": "104 Nguyễn Tất Thành, Phường 13, Quận 4",
    "Bưu cục Khánh Hội (Q4)": "52 Lê Quốc Hưng, Phường 12, Quận 4",
    "Bưu cục Nguyễn Trãi (Q5)": "49 Nguyễn Trãi, Phường 2, Quận 5",
    "Bưu cục Quận 5": "26 Nguyễn Thi, Phường 13, Quận 5",
    "Bưu cục Quận 6": "88-90 Tháp Mười, Phường 2, Quận 6",
    "Bưu cục Tân Phong (Q7)": "565 Nguyễn Thị Thập, Phường Tân Phong, Quận 7",
    "Bưu cục Quận 7": "1441 Huỳnh Tấn Phát, Phường Phú Mỹ, Quận 7",
    "Bưu cục Chánh Hưng (Q8)": "Chung cư Phạm Thế Hiển Phường 4, Quận 8",
    "Bưu cục Quận 8": "428 Tùng Thiện Vương, Phường 13, Quận 8",
    "Bưu cục Quận 10": "157 Lý Thái Tổ, Phường 9, Quận 10",
    "Bưu cục Hoà Hưng (Q10)": "411 Cách Mạng Tháng Tám, Phường 13, Quận 10",
    "Bưu cục Phú Thọ (Q10)": "270Bis Lý Thường Kiệt, Phường 14, Quận 10",
    "Bưu cục Quận 11": "244 Minh Phụng, Phường 16, Quận 11",
    "Bưu cục Quang Trung (Q12)": "Đường Tô Ký, Phường Đông Hưng Thuận, Quận 12",
    "Bưu cục Tân Thới Nhất (Q12)": "44/6 Phan Văn Hớn, Phường Tân Thới Nhất, Quận 12",
    "Bưu cục An Khánh (Q2 cũ)": "D7/2A Trần Não, Phường Bình Khánh, Quận 2",
    "Bưu cục Bình Trưng (Q2 cũ)": "42 Nguyễn Duy Trinh, Phường Bình Trưng Tây, Quận 2",
    "Bưu cục Chợ Nhỏ (Q9 cũ)": "95 Man Thiện, Phường Hiệp Phú, Quận 9",
    "Bưu cục Phước Bình (Q9 cũ)": "45 Đại lộ 2, Phường Phước Bình, Quận 9",
    "Bưu cục Bình Triệu (Thủ Đức)": "705 Gò Dưa, Phường Tam Bình, Thủ Đức",
    "Bưu cục Linh Trung (Thủ Đức)": "16 Đường số 4, Phường Linh Trung, Thủ Đức",
    "Bưu cục Thủ Đức": "128A Kha Vạn Cân, Phường Trường Thọ, Thủ Đức",
    "Bưu cục Thị Nghè (Bình Thạnh)": "23 Xô Viết Nghệ Tĩnh, Phường 17, Bình Thạnh",
    "Bưu cục Bình Thạnh": "03 Phan Đăng Lưu, Phường 3, Bình Thạnh",
    "Bưu cục Phú Nhuận": "241 Phan Đình Phùng, Phường 15, Phú Nhuận",
    "Bưu cục Gò Vấp": "555 Lê Quang Định, Phường 1, Gò Vấp",
    "Bưu cục Lê Văn Thọ (Gò Vấp)": "56 Cây Trâm, Phường 9, Gò Vấp",
    "Bưu cục Tân Sơn Nhất (Tân Bình)": "2B/2 Bạch Đằng, Phường 2, Tân Bình",
    "Bưu cục Tân Bình": "288A Hoàng Văn Thụ, Phường 4, Tân Bình",
    "Bưu cục Chí Hòa (Tân Bình)": "695-697 Cách Mạng Tháng Tám, Phường 6, Tân Bình",
    "Bưu cục Gò Dầu (Tân Phú)": "Chung cư Gò Dầu 2, Phường Tân Sơn Nhì, Tân Phú",
    "Bưu cục Tân Phú": "90 Lô B Nguyễn Sơn, Phường Phú Thọ Hòa, Tân Phú",
    "Bưu cục Bình Hưng Hòa (Bình Tân)": "1026 Tân Kỳ Tân Quý, Phường Bình Hưng Hòa, Bình Tân",
    "Bưu cục Bưu Điện Trung Tâm Hóc Môn": "57/7 Lý Nam Đế, Thị trấn Hóc Môn, Hóc Môn",
    "Bưu cục Tân Phú Trung (Củ Chi)": "912 Quốc Lộ 22, Xã Tân Phú Trung, Củ Chi",
    "Bưu cục Bình Chánh": "E9/37 Nguyễn Hữu Trí, Thị trấn Tân Túc, Bình Chánh"
}

# THUẬT TOÁN TỰ ĐỘNG CHUYỂN ĐỔI ĐỊA CHỈ THÀNH TỌA ĐỘ GPS (GEOCODING)
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

# THUẬT TOÁN TÍNH PHƯƠNG HƯỚNG BẺ LÁI CHO BƯU TÁ
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
            instructions.append("↩️ **Rẽ phải** tại giao lộ phía trước theo phân tuyến hành trình.")
        elif 205 <= turn < 335:
            instructions.append("↪️ **Rẽ trái** ôm theo bùng binh hoặc ngã rẽ vào làn gom bưu chính.")
    instructions.append("🔴 **Đến nơi:** Địa điểm bàn giao hàng nằm ngay trước hướng di chuyển.")
    return instructions[:6]


# ==========================================
# THIẾT KẾ THANH TASKBAR ĐIỀU HƯỚNG (MỤC TABS)
# ==========================================
tab_enterprise, tab_routing, tab_status = st.tabs([
    "🏢 Doanh nghiệp Vietnam Post", 
    "🗺️ Tối ưu tuyến đường chỉ dẫn", 
    "📦 Xác nhận trạng thái đơn"
])

# ------------------------------------------
# MỤC 1: DOANH NGHIỆP VIETNAM POST (TỔNG QUAN & ĐIỀU HÀNH)
# ------------------------------------------
with tab_enterprise:
    st.header("Tổng công ty Bưu điện Việt Nam - Vietnam Post")
    
    hub_selected = st.selectbox("Lựa chọn bưu cục quản lý hệ thống:", list(VNPOST_HUBS.keys()))
    st.info(f"💡 **Vị trí địa lý:** {VNPOST_HUBS[hub_selected]}")
    
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.markdown("### 📊 Tiến độ khai thác sản lượng trong ngày")
        st.write("Tỷ lệ bưu phẩm đã phát thành công chặng cuối:")
        st.progress(0.85)
        
        st.markdown("---")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric(label="Đơn hàng phát thành công", value="1,420 kiện", delta="+12%")
        col_m2.metric(label="Bưu tá thực địa chặng cuối", value="45 nhân sự", delta="Sẵn sàng")
        
    with col_info2:
        with st.container(border=True):
            st.write("🎯 **Quản lý Tải trọng & Khuyến cáo phân loại bưu phẩm**")
            st.warning("⚠️ Hệ thống phát hiện có **24 bưu phẩm cồng kềnh/dễ vỡ** có kích thước vượt giỏ hàng xe máy thông thường.")
            st.write("- 🛵 **Xe máy bưu tá:** Phù hợp với bưu phẩm thư từ, tài liệu hoặc gói hàng < 5kg.")
            st.write("- 🚚 **Xe tải bưu chính nhỏ (1.25 Tấn):** Đã phân bổ 2 xe hỗ trợ đi gom gom các tuyến đường trục lớn để tránh hư hỏng hàng hóa.")

# ------------------------------------------
# MỤC 2: TỐI ƯU TUYẾN ĐƯỜNG CHỈ DẪN (ĐỊNH TUYẾN THÔNG MINH)
# ------------------------------------------
with tab_routing:
    st.header("Hệ thống tối ưu đường đi thực địa bưu chính")
    
    st.sidebar.header("🛠️ Cấu hình lộ trình chặng phát")
    
    # Cho phép chọn nhanh bưu cục xuất phát từ danh sách chuẩn dữ liệu vừa cung cấp
    selected_start_hub = st.sidebar.selectbox("Chọn nhanh bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
    start_address = VNPOST_HUBS[selected_start_hub]
    
    st.sidebar.text("📍 Địa chỉ bưu cục tự động điền:")
    start_input = st.sidebar.text_area("Từ bưu cục:", value=start_address, height=70)
    
    end_input = st.sidebar.text_input("Địa chỉ phát hàng của khách (Ví dụ: 100 Cao Thắng):", "100 Cao Thắng")
    
    vehicle_type = st.sidebar.radio("Lựa chọn phương tiện vận chuyển:", ["🛵 Xe máy bưu tá chặng cuối", "🚚 Xe tải bưu chính lớn"])
    
    st.sidebar.markdown("---")
    activated = st.sidebar.button("🚀 Tính toán lộ trình thực địa")

    col_left, col_right = st.columns([2, 1])

    default_lat, default_lon = 10.7760, 106.7032
    m = folium.Map(location=[default_lat, default_lon], zoom_start=14, control_scale=True)
    folium.TileLayer('openstreetmap', name='Bản đồ đường phố').add_to(m)

    if activated:
        if not start_input.strip() or not end_input.strip():
            st.sidebar.warning("⚠️ Vui lòng điền đủ thông tin địa chỉ gửi và nhận!")
        elif start_input.strip().lower() == end_input.strip().lower():
            st.sidebar.warning("⚠️ Vị trí xuất phát và đích đến không được trùng nhau!")
        else:
            try:
                with st.spinner("🔍 Đang kết nối OSRM tính toán định tuyến bám đường phố..."):
                    folium_static, Fullscreen = get_advanced_libraries()
                    loc1 = get_coordinates_from_address(start_input)
                    loc2 = get_coordinates_from_address(end_input)
                    
                    if not loc1:
                        st.error(f"❌ Không tìm thấy vị trí bưu cục: '{start_input}'")
                    elif not loc2:
                        st.error(f"❌ Không tìm thấy vị trí khách hàng: '{end_input}'")
                    else:
                        profile = "driving"
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
                            Fullscreen(position="topleft", title="Mở rộng").add_to(m)
                            folium.TileLayer('openstreetmap').add_to(m)
                            
                            folium.Marker([loc1['lat'], loc1['lon']], tooltip=f"Xuất phát: {loc1['display_name']}", icon=folium.Icon(color='green', icon='play')).add_to(m)
                            folium.Marker([loc2['lat'], loc2['lon']], tooltip=f"Điểm phát: {loc2['display_name']}", icon=folium.Icon(color='red', icon='flag')).add_to(m)
                            folium.PolyLine(detailed_route_gps, color="#0056b3", weight=6, opacity=0.85).add_to(m)
                            
                            st.success("✅ Tuyến đường bưu chính đã được tối ưu hóa thành công!")
                            
                            with col_left:
                                st.write(f"🗺️ **Tuyến đường bưu chính bám sát lòng đường:**")
                                folium_static(m, width=800, height=520)
                                
                                gps_text = f"Lộ trình hành trình: {selected_start_hub} -> {end_input} | Tổng khoảng cách: {distance_km:.2f} km."
                                st.text_input("Chuỗi dữ liệu định vị (Dùng để đồng bộ):", value=gps_text)
                                
                            with col_right:
                                st.write("📱 **Màn hình điều hướng bưu tá:**")
                                with st.container(border=True):
                                    st.metric(label="Tổng chiều dài chặng phát", value=f"{total_distance:.0f} mét")
                                    st.metric(label="Thời gian di chuyển dự kiến", value=f"{duration/60:.1f} phút")
                                    st.metric(label="Ước tính phụ cấp nhiên liệu chặng", value=f"{fuel_consumption:.0f} VNĐ")
                                    st.markdown("---")
                                    st.write("🧭 **Chỉ dẫn lộ trình chi tiết:**")
                                    for inst in nav_instructions:
                                        st.write(inst)
                        else:
                            st.error("❌ Máy chủ định tuyến không tìm thấy tuyến đường khả thi.")
            except Exception as e:
                st.error(f"❌ Lỗi xử lý dữ liệu: {e}")
    else:
        with col_left:
            st.write("🗺️ **Bản đồ tương tác thực địa mạng lưới bưu chính:**")
            try:
                from streamlit_folium import folium_static
                folium_static(m, width=800, height=520)
            except Exception:
                st.warning("Đang khởi tạo bản đồ hệ thống...")
        with col_right:
            st.write("📱 **Màn hình điều hướng bưu tá:**")
            st.info("Nhập địa chỉ ở cột bên trái và bấm nút 'Tính toán lộ trình thực địa'.")

# ------------------------------------------
# MỤC 3: XÁC NHẬN TRẠNG THÁI ĐƠN HÀNG (QUẢN LÝ CHẶNG CUỐI)
# ------------------------------------------
with tab_status:
    st.header("Trung tâm Quản lý & Đối soát Vận đơn Chặng cuối")
    
    st.write("📋 **Danh sách các vận đơn bưu chính được phân bổ cho bạn hôm nay:**")
    mock_orders = {
        "Mã Vận Đơn": ["VN94827HCM", "VN10482HCM", "VN58291HCM", "VN30294HCM"],
        "Người Nhận": ["Nguyễn Văn A", "Trần Thị B", "Lê Hoàng C", "Phạm Minh D"],
        "Địa Chỉ": ["100 Cao Thắng, Q3", "320 Nguyễn Du, Q1", "Hồ Con Rùa, Q3", "Vòng xoay Dân Chủ"],
        "Loại Hàng": ["Tài liệu mật", "Hàng linh kiện điện tử", "Bưu kiện cồng kềnh", "Hàng dễ vỡ"]
    }
    df_orders = pd.DataFrame(mock_orders)
    st.dataframe(df_orders, use_container_width=True)
    
    st.markdown("---")
    
    col_status1, col_status2 = st.columns([1, 1])
    with col_status1:
        st.write("🆔 **Cập nhật nhanh tiến độ đơn phát**")
        selected_order = st.selectbox("Chọn mã vận đơn cần xử lý từ danh sách trên:", df_orders["Mã Vận Đơn"])
        
        status_options = [
            "🛵 Bưu tá đang đi phát hàng chặng cuối",
            "✅ Phát thành công (Đã ký nhận)",
            "❌ Giao hàng thất bại / Khách hẹn lại ngày phát",
            "🚨 Báo cáo sự cố khẩn cấp trên tuyến đường (SOS)"
        ]
        current_status = st.selectbox("Cập nhật trạng thái mới cho bưu phẩm:", status_options, index=0)
        
        if "Thất bại" in current_status:
            fail_reason = st.selectbox("Lý do giao hàng thất bại cụ thể:", [
                "Khách hàng tắt máy, không liên lạc được (Quá 3 lần gọi)",
                "Khách hàng hẹn đổi sang ca chiều / ngày mai",
                "Sai thông tin số nhà, địa chỉ không tồn tại",
                "Khách hàng từ chối nhận bưu phẩm do đổi ý"
            ])
            
        elif "Thành công" in current_status:
            st.success("Tích hợp hồ sơ POD - Vui lòng lưu bằng chứng phát hành bên dưới:")
            st.file_uploader("📸 Tải lên ảnh chụp ký nhận thực tế tại nhà khách (Bằng chứng POD):", type=["jpg", "png", "jpeg"])
            st.text_input("Họ tên người ký nhận thay (nếu có):")
            
        elif "SOS" in current_status:
            st.error("🚨 HỆ THỐNG CẢNH BÁO SỰ CỐ KHẨN CẤP")
            sos_reason = st.text_area("Mô tả chi tiết sự cố thực địa (Ví dụ: Xe hỏng hóc, tai nạn, ngập lụt nghiêm trọng...):", 
                                      "Bị thủng lốp xe trên đường trục chính, cần đội kỹ thuật bưu cục hỗ trợ ứng ứng.")
            st.caption("ℹ️ Khi bấm xác nhận SOS, hệ thống sẽ tự động gửi tọa độ của bạn về bưu cục trung tâm và tạm hoãn các đơn hàng còn lại trong ca.")
            
        note = st.text_area("Ghi chú bổ sung của bưu tá:", "Đang di chuyển tiếp cận.")
        
        if st.button("💾 Xác nhận và Đồng bộ lên Tổng đài VNPost"):
            st.toast(f"Đã đồng bộ dữ liệu vận đơn {selected_order} thành công!", icon="🚀")
            st.success(f"Dữ liệu trạng thái của mã đơn {selected_order} đã được truyền lên hệ thống quản trị trung tâm.")
            
    with col_status2:
        st.write("🕒 **Lịch sử cập nhật hệ thống (Timeline)**")
        with st.container(border=True):
            st.markdown(f"**Mã vận đơn đang kiểm tra:** `{selected_order}`")
            st.markdown("---")
            st.markdown(f"📍 **Trạng thái ghi nhận gần nhất:** `{current_status}`")
            st.markdown("---")
            st.write("📜 **Dòng thời gian chi tiết:**")
            st.markdown(f"- **[2026-07-09 09:35]** Trạng thái: {current_status} | Ghi chú: *{note}*")
            st.markdown("- **[2026-07-09 06:15]** Trạng thái: *📥 Đã nhập kho bưu cục chặng cuối* (Địa điểm: Trung tâm khai thác phân loại bưu chính TP.HCM).")
            st.markdown("- **[2026-07-08 14:20]** Trạng thái: *🚚 Đang vận chuyển liên tỉnh* (Tuyến vận chuyển: Trục bưu chính quốc gia Bắc Nam).")
