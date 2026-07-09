import streamlit as st
import folium
import math
import requests
import pandas as pd
import numpy as np
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

# 3. THIẾT LẬP THANH SIDEBAR CẤU HÌNH LỘ TRÌNH
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
# TAB 1: TRUNG TÂM GIÁM SÁT (NÂNG CẤP BIỂU ĐỒ TRỰC QUAN)
# ------------------------------------------
with tab_enterprise:
    st.markdown("""### 📊 Tổng quan Hoạt động Mạng lưới""")
    st.markdown(f"<div style='background-color:#e0f2fe; padding:12px; border-radius:8px; border-left:4px solid #0284c7; color:#0369a1;'>📍 <b>Bưu cục đang giám sát:</b> {selected_start_hub} — <b>Địa chỉ:</b> {VNPOST_HUBS[selected_start_hub]}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Khu vực thẻ số liệu nhanh (KPI Cards)
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown("""<div class="metric-card"><p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:bold;">ĐÃ GIAO THÀNH CÔNG</p><h2 style="margin:5px 0 0 0; color:#0056b3; font-weight:800;">1,420 kiện</h2><p style="margin:0; font-size:0.85rem; color:#16a34a;">↗️ +12% so với hôm qua</p></div>""", unsafe_allow_html=True)
    with col_m2:
        st.markdown("""<div class="metric-card"><p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:bold;">BƯU TÁ THỰC ĐỊA</p><h2 style="margin:5px 0 0 0; color:#0056b3; font-weight:800;">45 Nhân sự</h2><p style="margin:0; font-size:0.85rem; color:#0284c7;">🔵 Trạng thái: Sẵn sàng</p></div>""", unsafe_allow_html=True)
    with col_m3:
        st.markdown("""<div class="metric-card"><p style="margin:0; font-size:0.9rem; color:#64748b; font-weight:bold;">TỶ LỆ TOÀN TRÌNH POD</p><h2 style="margin:5px 0 0 0; color:#e67e22; font-weight:800;">94.8 %</h2><p style="margin:0; font-size:0.85rem; color:#64748b;">⏱️ Cập nhật: Vừa xong</p></div>""", unsafe_allow_html=True)

    st.markdown("---")
    
    # KHU VỰC THỂ HIỆN BIỂU ĐỒ PHÂN TÍCH (ANALYTICS DASHBOARD)
    col_chart1, col_chart2 = st.columns([1, 1])
    
    with col_chart1:
        st.markdown("#### 📈 Tỷ lệ giao hàng thành công theo khu vực (Quận)")
        # Tạo dữ liệu mẫu tỉ lệ đơn hàng thành công và thất bại theo khu vực
        chart_data_district = pd.DataFrame({
            "Thành công (Đã ký POD)": [420, 380, 290, 180, 150],
            "Đang phát/Hoãn lại": [15, 22, 12, 8, 19]
        }, index=["Quận 1", "Quận 3", "Quận 5", "Quận 7", "Quận 4"])
        
        # Hiển thị biểu đồ cột chồng (Stacked Bar Chart)
        st.bar_chart(chart_data_district, color=["#0056b3", "#ffc745"])
        st.caption("Biểu đồ so sánh số lượng đơn phát thành công trực quan giữa các cụm bưu cục chặng cuối.")

    with col_chart2:
        st.markdown("#### 🚚 Biểu đồ xu hướng tải trọng vận chuyển trong tuần")
        # Tạo dữ liệu mẫu xu hướng tải trọng (Tấn) theo ngày trong tuần của 2 đội xe
        chart_data_weight = pd.DataFrame({
            "Đội xe máy chặng cuối": [2.1, 2.8, 3.2, 2.9, 3.5, 4.1, 1.5],
            "Đội xe tải bưu chính": [8.5, 9.2, 11.0, 10.1, 12.4, 14.0, 5.0]
        }, index=["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"])
        
        # Hiển thị biểu đồ miền xu hướng (Area Chart)
        st.area_chart(chart_data_weight, color=["#22c55e", "#ef4444"])
        st.caption("Khối lượng tải trọng hàng hóa biến động (Đơn vị: Tấn) phân bổ theo lịch trình tuần hành.")

    st.markdown("---")
    with st.container(border=True):
        st.markdown("""🎯 **Khuyến cáo Điều phối từ Hệ thống trí tuệ nhân tạo:**""")
        st.warning("⚠️ Dự báo cao điểm: Tải trọng khu vực **Quận 1** và **Quận 3** tăng mạnh vào ngày Thứ 6 và Thứ 7. Đề xuất tăng cường thêm 15% nhân sự bưu tá chặng cuối.")

# ------------------------------------------
# TAB 2: TỐI ƯU TUYẾN ĐƯỜNG (BẢN ĐỒ)
# ------------------------------------------
with tab_routing:
    st.markdown("""### 🗺️ Bản đồ Định tuyến & Tối ưu lộ trình bưu tá""")
    
    col_left, col_right = st.columns([1.8, 1.2])
    
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
                        lon1, lat1 = loc1['lon'], loc1['lat']
                        lon2, lat2 = loc2['lon'], loc2['lat']
                        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
                        response = requests.get(url).json()
                        
                        if response.get('code') == 'Ok':
                            route_data = response['routes'][0]
                            detailed_route_gps = [[c[1], c[0]] for c in route_data['geometry']['coordinates']]
                            distance_km = route_data['distance'] / 1000
                            duration_min = route_data['duration'] / 60
                            fuel = (distance_km / 100) * (2.5 if "🛵" in vehicle_type else 9.0) * 23000
                            
                            m = folium.Map(location=[(lat1+lat2)/2, (lon1+lon2)/2], zoom_start=15)
                            folium.Marker([lat1, lon1], tooltip="Bưu cục phát", icon=folium.Icon(color='green', icon='play')).add_to(m)
                            folium.Marker([lat2, lon2], tooltip="Địa chỉ khách hàng", icon=folium.Icon(color='red', icon='flag')).add_to(m)
                            folium.PolyLine(detailed_route_gps, color="#0056b3", weight=6, opacity=0.8).add_to(m)
                            
                            with col_left:
                                st.markdown("""<div style='color:#15803d; font-weight:bold; margin-bottom:5px;'>✅ ĐÃ TỐI ƯU TUYẾN ĐƯỜNG THÀNH CÔNG</div>""", unsafe_allow_html=True)
                                folium_static(m, width=700, height=480)
                            with col_right:
                                st.markdown("""##### 📱 Kết quả điều hành thực địa""")
                                with st.container(border=True):
                                    st.write(f"🛣️ **Quãng đường:** `{distance_km:.2f} km`")
                                    st.write(f"⏱️ **Thời gian di chuyển dự kiến:** `{duration_min:.1f} phút`")
                                    st.write(f"💰 **Chi phí nhiên liệu định mức:** `{fuel:.0f} VNĐ`")
                                    st.markdown("---")
                                    st.markdown("**🗺️ Chỉ đường chi tiết từng chặng:**")
                                    for inst in generate_turn_by_turn(detailed_route_gps):
                                        st.write(inst)
                        else:
                            with col_left:
                                st.error("❌ Máy chủ định tuyến từ chối kết nối hoặc không tìm thấy lộ trình đường đi khả thi.")
                                folium_static(m, width=700, height=480)
            except Exception as e:
                with col_left:
                    st.error(f"❌ Sự cố hệ thống bản đồ: {e}")
                    folium_static(m, width=700, height=480)
    else:
        with col_left:
            folium_static(m, width=700, height=480)
        with col_right:
            st.info("💡 Hãy điền thông tin địa chỉ tại Sidebar bên trái và nhấn nút 'Tính toán lộ trình thực địa' để bắt đầu.")

# ------------------------------------------
# TAB 3: QUẢN LÝ TRẠNG THÁI VẬN ĐƠN
# ------------------------------------------
with tab_status:
    st.markdown("""### 📦 Quản lý Trạng thái Vận đơn Chặng cuối""")
    
    mock_orders = {
        "Mã Vận Đơn": ["VN94827HCM", "VN10482HCM", "VN58291HCM", "VN30294HCM"],
        "Người Nhận": ["Nguyễn Văn A", "Trần Thị B", "Lê Hoàng C", "Phạm Minh D"],
        "Địa Chỉ":
