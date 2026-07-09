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
    </style>""", 
    unsafe_allow_html=True
)

# Đầy đủ danh sách bưu cục gốc của bạn
VNPOST_HUBS = {
    "Bưu cục Tân Định (Q1)": {"address": "230 Hai Bà Trưng, Q1", "lat": 10.7891, "lon": 106.6910},
    "Bưu cục Giao dịch Sài Gòn (Q1)": {"address": "2 Công xã Paris, Q1", "lat": 10.7798, "lon": 106.6999},
    "Bưu cục Quận 3": {"address": "2Bis Bà Huyện Thanh Quan, Q3", "lat": 10.7770, "lon": 106.6853},
    "Bưu cục Bàn Cờ (Q3)": {"address": "49A Cao Thắng, Q3", "lat": 10.7745, "lon": 106.6811},
    "Bưu cục Quận 5": {"address": "26 Nguyễn Thị, Q5", "lat": 10.7512, "lon": 106.6631},
    "Bưu cục Quận 7": {"address": "1441 Huỳnh Tấn Phát, Q7", "lat": 10.7351, "lon": 106.7323}
}

POPULAR_STOPS = {
    "120 cách mạng tháng tám": [10.7792, 106.6881],
    "240 điện biên phủ": [10.7865, 106.6915],
    "312 võ thị sáu": [10.7849, 106.6872],
    "02 võ oanh": [10.8021, 106.7142],
    "100 cao thắng": [10.7745, 106.6811],
    "320 nguyễn du": [10.7712, 106.6945],
    "hồ con rùa": [10.7827, 106.6961]
}

if "map_ready" not in st.session_state: st.session_state.map_ready = False
if "lines_cache" not in st.session_state: st.session_state.lines_cache = []
if "text_cache" not in st.session_state: st.session_state.text_cache = []

with st.sidebar:
    st.write("### CẤU HÌNH PHÂN TUYẾN")
    selected_hub = st.selectbox("Chọn bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
    st.text_area("Địa chỉ bưu cục điều phối:", value=VNPOST_HUBS[selected_hub]["address"], height=70, disabled=True)
    st.write("---")
    stops_input = st.text_area(
        "Các điểm dừng phát hàng (1 dòng/địa chỉ):", 
        value="120 Cách Mạng Tháng Tám\n240 Điện Biên Phủ\n312 Võ Thị Sáu\n02 Võ Oanh", 
        height=120
    )
    vehicle_type = st.radio("Phương tiện vận chuyển:", ["Xe máy bưu tá chặng cuối", "Xe tải bưu chính lớn"])
    
    if st.button("TỐI ƯU LỘ TRÌNH THỰC ĐỊA"):
        st.session_state.map_ready = True
        st.session_state.lines_cache = []
        st.session_state.text_cache = []

st.markdown('<p class="main-title">VIETNAM POST - ĐIỀU HÀNH LOGISTICS ĐA ĐIỂM</p>', unsafe_allow_html=True)
tab_monitor, tab_map, tab_order = st.tabs(["Trung tâm Giám sát", "Tối ưu Tuyến đường Đa điểm", "Quản lý Vận đơn"])

with tab_monitor:
    st.write(f"**Đang giám sát:** {selected_hub}")
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="metric-card"><b>ĐA GIAO POD</b><h3 style="color:#0056b3;margin:0;">1.420 kiện</h3></div>', unsafe_allow_html=True)
    c2.markdown('<div class="metric-card"><b>BƯU TÁ THỰC ĐỊA</b><h3 style="color:#0056b3;margin:0;">45 Nhân sự</h3></div>', unsafe_allow_html=True)
    c3.markdown('<div class="metric-card"><b>TỶ LỆ TOÀN TRÌNH</b><h3 style="color:#e67e22;margin:0;">94.8 %</h3></div>', unsafe_allow_html=True)

with tab_map:
    st.write("### Bản đồ điều phối chuỗi điểm giao hàng")
    col_left, col_right = st.columns([1.8, 1.2])
    h_lat, h_lon = VNPOST_HUBS[selected_hub]["lat"], VNPOST_HUBS[selected_hub]["lon"]
    
    m = folium.Map(location=[h_lat, h_lon], zoom_start=13)
    Fullscreen(position="topleft", title="Mở rộng", title_cancel="Thoát", force_separate_button=True).add_to(m)
    folium.Marker([h_lat, h_lon], tooltip="BƯU CỤC XUẤT PHÁT", icon=folium.Icon(color='green', icon='play')).add_to(m)

    if st.session_state.map_ready:
        raw_lines = [line.strip().lower() for line in stops_input.split('\n') if line.strip()]
        base_coords = [[h_lon, h_lat]]
        
        for stop_addr in raw_lines:
            for k, coords in POPULAR_STOPS.items():
                if k in stop_addr:
                    base_coords.append([coords[1], coords[0]])
                    folium.Marker([coords[0], coords[1]], tooltip=k, icon=folium.Icon(color='blue')).add_to(m)

        if len(base_coords) > 1 and not st.session_state.lines_cache:
            try:
                coord_str = ";".join([f"{c[0]},{c[1]}" for c in base_coords])
                url = (
                    f"http://router.project-osrm.org/trip/v1/driving/{coord_str}"
                    f"?source=first&destination=any&overview=full&geometries=geojson"
                )
                res = requests.get(url, timeout=5).json()
                if res.get('code') == 'Ok':
                    raw_pts = res['trips'][0]['geometry']['coordinates']
                    st.session_state.lines_cache = [[p[1], p[0]] for p in raw_pts]
                    dist_km = res['trips'][0]['distance'] / 1000
                    time_mn = res['trips'][0]['duration'] / 60
                    fuel_rate = 2.5 if "máy" in vehicle_type else 9.0
                    cost = (dist_km / 100) * fuel_rate * 23000
                    st.session_state.text_cache = [
                        f"Tổng quãng đường: {dist_km:.2f} km",
                        f"Ước tính thời gian: {time_mn:.1f} phút",
                        f"Chi phí nhiên liệu: {cost:.0f} VND"
                    ]
            except Exception as e:
                st.session_state.lines_cache = []

        if st.session_state.lines_cache:
            folium.PolyLine(st.session_state.lines_cache, color="#0056b3", weight=6, opacity=0.9).add_to(m)
            with col_right:
                st.write("##### THÔNG TIN LỘ TRÌNH ĐÃ TỐI ƯU")
                for txt in st.session_state.text_cache: st.info(txt)
        else:
            with col_right: st.warning("Đã hiển thị các điểm ghim dữ liệu.")
    else:
        with col_right: st.info("Nhấn nút tối ưu bên trái để vẽ tuyến đường thực địa!")

    with col_left: st_folium(m, width=700, height=450, key="vnpost_map_v7_final")

with tab_order:
    st.write("### Danh sách kiểm soát bưu kiện")
    st.write("- VN94827HCM: Đang vận chuyển chặng cuối")
    st.write("- VN10482HCM: Đang vận chuyển chặng cuối")
