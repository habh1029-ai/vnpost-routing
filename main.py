import streamlit as st
import folium
from folium.plugins import Fullscreen
import requests
import pandas as pd
from streamlit_folium import st_folium

st.set_page_config(page_title="VNPOST Logistics", layout="wide")

st.markdown("""<style>.main-title { font-size: 2rem; font-weight: 800; color: #0056b3; border-bottom: 4px solid #F2A900; padding-bottom: 10px; } .metric-card { background: #f8fafc; border-left: 5px solid #F2A900; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); } div.stButton > button { background: #F2A900; color: #003366!important; font-weight: bold; width: 100%; }</style>""", unsafe_allow_html=True)

VNPOST_HUBS = {"Bưu cục Tân Định (Q1)": {"address": "230 Hai Bà Trưng, Q1", "lat": 10.7891, "lon": 106.6910}, "Bưu cục Giao dịch Sài Gòn (Q1)": {"address": "2 Công xã Paris, Q1", "lat": 10.7798, "lon": 106.6999}, "Bưu cục Quận 3": {"address": "2Bis Bà Huyện Thanh Quan, Q3", "lat": 10.7770, "lon": 106.6853}}
POPULAR_STOPS = {"120 cách mạng tháng tám": [10.7792, 106.6881], "240 điện biên phủ": [10.7865, 106.6915], "312 võ thị sáu": [10.7849, 106.6872], "02 võ oanh": [10.8021, 106.7142]}

if "map_ready" not in st.session_state: st.session_state.map_ready = False
if "lines_cache" not in st.session_state: st.session_state.lines_cache = []
if "text_cache" not in st.session_state: st.session_state.text_cache = []

with st.sidebar:
    st.write("### CẤU HÌNH PHÂN TUYẾN")
    selected_hub = st.selectbox("Chọn bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
    stops_input = st.text_area("Các điểm dừng phát hàng (1 dòng/ địa chỉ):", value="120 Cách Mạng Tháng Tám\n240 Điện Biên Phủ\n312 Võ Thị Sáu\n02 Võ Oanh", height=120)
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
    st.write("### Bản đồ điều phối chuỗi điểm giao hàng (Giải thuật TSP tự động gom điểm gần)")
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
                url = f"http://router.project-osrm.org/trip/v1/driving/{coord_str}?source=first&destination=any&overview=full&geometries=geojson"
                res = requests.get(url, timeout=5).json()
                if res.get('code') == 'Ok':
                    st.session_state.lines_cache = [[c[1], c[0]] for c in res
