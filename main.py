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

MOCK_ORDERS = {
    "Mã Vận Đơn": ["VN94827HCM", "VN10482HCM", "VN58291HCM"],
    "Người Nhận": ["Nguyễn Văn A", "Trần Thị B", "Lê Hoàng C"],
    "Địa Chỉ Giao Hàng": ["100 Cao Thắng, Q3", "320 Nguyễn Du, Q1", "Hồ Con Rùa, Q3"],
    "Loại Hàng Hóa": ["Tài liệu mật", "Linh kiện điện tử", "Bưu kiện lớn"]
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
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown('<div class="metric-card"><p style="color:#64748b; font-weight:bold; margin:0;">ĐA GIAO POD</p><h3 style="margin:5px 0 0 0; color:#0056b3;">1.420 kiện</h3></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown('<div class="metric-card"><p style="color:#64748b; font-weight:bold; margin:0;">BƯU TÁ THỰC ĐỊA</p><h3 style="margin:5px 0 0 0; color:#0056b3;">45 Nhân sự</h3></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown('<div class="metric-card"><p style="color:#64748b; font-weight:bold; margin:0;">TỶ LỆ TOÀN TRÌNH</p><h3 style="margin:5px 0 0 0; color:#e67e22;">94.8 %</h3></div>', unsafe_allow_html=True)

    st.write("---")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.write("#### Sản lượng giao thành công theo quận")
        st.bar_chart(pd.DataFrame(DISTRICT_DATA, index=DISTRICT_INDEX), color=["#0056b3", "#ffc745"])
    with col_c2:
        st.write("#### Trọng tải vận chuyển trong tuần (Tấn)")
        st.area_chart(pd.DataFrame(WEIGHT_DATA, index=WEIGHT_INDEX), color=["#22c55e", "#ef4444"])

# ------------------------------------------
# TAB 2: TỐI ƯU TUYẾN ĐƯỜNG ĐA ĐIỂM & BẢN ĐỒ
# ------------------------------------------
with tab_map:
    st.write("### Bản đồ điều phối chuỗi điểm giao hàng cho tài xế")
    col_left, col_right = st.columns([1.8, 1.2])
    
    # Khởi tạo bản đồ nền tại trung tâm TP.HCM
    m = folium.Map(location=[10.7760, 106.7032], zoom_start=13)

    if activated:
        raw_stops = [line.strip() for line in stops_input.split('\n') if line.strip()]
        if start_input.strip() and raw_stops:
            try:
                start_loc = get_coordinates_from_address(start_input)
                if start_loc:
                    all_coordinates = [[start_loc['lat'], start_loc['lon']]]
                    valid_names = ["Bưu cục xuất phát"]
                    
                    # Duyệt danh sách tìm tọa độ các điểm dừng chân
                    for idx, stop_addr in enumerate(raw_stops, 1):
                        loc = get_coordinates_from_address(stop_addr)
                        if loc:
                            all_coordinates.append([loc['lat'], loc['lon']])
                            valid_names.append(f"Điểm {idx}: {stop_addr}")
                    
                    if len(all_coordinates) >= 2:
                        total_dist = 0.0
                        total_time = 0.0
                        m = folium.Map(location=all_coordinates[0], zoom_start=14)
                        
                        # Điểm khởi hành (Xanh lá)
                        folium.Marker(all_coordinates[0], tooltip="XUẤT PHÁT", icon=folium.Icon(color='green', icon='play')).add_to(m)
                        
                        # Vẽ định tuyến chuỗi điểm nối tiếp nhau (OSRM API)
                        for i in range(len(all_coordinates) - 1):
                            p_start = all_coordinates[i]
                            p_end = all_coordinates[i+1]
                            
                            folium.Marker(p_end, tooltip=valid_names[i+1], icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
                            
                            url = f"http://router.project-osrm.org/route/v1/driving/{p_start[1]},{p_start[0]};{p_end[1]},{p_end[0]}?overview=full&geometries=geojson"
                            res = requests.get(url).json()
                            
                            if res.get('code') == 'Ok':
                                chunk = res['routes'][0]
                                gps_coords = [[c[1], c[0]] for c in chunk['geometry']['coordinates']]
                                total_dist += chunk['distance'] / 1000
                                total_time += chunk['duration'] / 60
                                folium.PolyLine(gps_coords, color="#0056b3", weight=5, opacity=0.8).add_to(m)
                        
                        fuel_rate = 2.5 if "máy" in vehicle_type else 9.0
                        fuel_cost = (total_dist / 100) * fuel_rate * 23000
                        
                        with col_left:
                            folium_static(m, width=700, height=450)
                        with col_right:
                            st.write("##### THÔNG TIN HÀNH TRÌNH")
                            st.info(f"Tổng quãng đường: {total_dist:.2f} km\n\nThời gian dự kiến: {total_time:.1f} phút\n\nChi phí nhiên liệu: {fuel_cost:.0f} VND")
                            st.write("---")
                            st.write("**Thứ tự lịch trình di chuyển:**")
                            for name in valid_names:
                                st.write(f"- {name}")
                else:
                    st.error("Không định vị được địa chỉ bưu cục xuất phát.")
            except Exception as e:
                st.error(f"Lỗi hệ thống bản đồ hành trình: {e}")
        else:
            with col_left:
                folium_static(m, width=700, height=450)
    else:
        with col_left:
            folium_static(m, width=700, height=450)
        with col_right:
            st.info("Vui lòng điền danh sách các địa chỉ dừng nhận ở thanh điều hướng bên trái và nhấn nút để phân tích.")

# ------------------------------------------
# TAB 3: QUẢN LÝ VẬN ĐƠN BƯU KIỆN
# ------------------------------------------
with tab_order:
    st.write("### Danh sách kiểm soát bưu kiện chặng cuối")
    st.dataframe(pd.DataFrame(MOCK_ORDERS), use_container_width=True)
