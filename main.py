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
    .status-delivery { background-color: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .status-success { background-color: #dcfce7; color: #15803d; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .status-pending { background-color: #fef3c7; color: #b45309; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
    .timeline-item { border-left: 3px solid #0056b3; padding-left: 15px; margin-bottom: 15px; position: relative; }
    .timeline-time { font-size: 0.85rem; color: #64748b; font-weight: bold; }
    </style>""", 
    unsafe_allow_html=True
)

def get_osrm_trip(coord_str):
    try:
        url = f"http://router.project-osrm.org/trip/v1/driving/{coord_str}?source=first&destination=any&overview=full&geometries=geojson"
        return requests.get(url, timeout=5).json()
    except:
        return None

# Hệ thống dữ liệu viết liền dòng - chống lỗi bẻ dòng trên Cloud tuyệt đối
VNPOST_HUBS = {"Bưu cục Tân Định (Q1)": {"address": "230 Hai Bà Trưng, Q1", "lat": 10.7891, "lon": 106.6910}, "Bưu cục Giao dịch Sài Gòn (Q1)": {"address": "2 Công xã Paris, Q1", "lat": 10.7798, "lon": 106.6999}, "Bưu cục Quận 3": {"address": "2Bis Bà Huyện Thanh Quan, Q3", "lat": 10.7770, "lon": 106.6853}, "Bưu cục Bàn Cờ (Q3)": {"address": "49A Cao Thắng, Q3", "lat": 10.7745, "lon": 106.6811}, "Bưu cục Quận 5": {"address": "26 Nguyễn Thị, Q5", "lat": 10.7512, "lon": 106.6631}, "Bưu cục Quận 7": {"address": "1441 Huỳnh Tấn Phát, Q7", "lat": 10.7351, "lon": 106.7323}}

# ĐÃ BỔ SUNG TỌA ĐỘ CÁC ĐIỂM MỚI TRÊN ĐƯỜNG XÔ VIẾT NGHỆ TĨNH TRÁNH BỊ BỎ SÓT CHẶNG
POPULAR_STOPS = {"120 cách mạng tháng tám": [10.7792, 106.6881], "240 điện biên phủ": [10.7865, 106.6915], "312 võ thị sáu": [10.7849, 106.6872], "670 xô viết nghệ tĩnh": [10.8038, 106.7115], "760/5 xô viết nghệ tĩnh": [10.8055, 106.7128], "02 võ oanh": [10.8021, 106.7142], "100 cao thắng": [10.7745, 106.6811], "320 nguyễn du": [10.7712, 106.6945]}

if "map_ready" not in st.session_state: st.session_state.map_ready = False
if "lines_cache" not in st.session_state: st.session_state.lines_cache = []
if "text_cache" not in st.session_state: st.session_state.text_cache = []
if "steps_cache" not in st.session_state: st.session_state.steps_cache = []

# Đồng bộ danh sách quản lý vận đơn đầy đủ 6 đơn tương ứng với 6 điểm phát hàng
if "orders_db" not in st.session_state:
    st.session_state.orders_db = [
        {"Mã đơn": "VN94827HCM", "Người nhận": "Nguyễn Văn A", "Địa chỉ": "120 Cách Mạng Tháng Tám", "COD": "250.000đ", "Trạng thái": "🚚 Đang giao hàng"},
        {"Mã đơn": "VN10482HCM", "Người nhận": "Trần Thị B", "Địa chỉ": "240 Điện Biên Phủ", "COD": "0đ (Đã TT)", "Trạng thái": "🚚 Đang giao hàng"},
        {"Mã đơn": "VN88301HCM", "Người nhận": "Phạm Minh C", "Địa chỉ": "312 Võ Thị Sáu", "COD": "120.000đ", "Trạng thái": "✅ Giao thành công"},
        {"Mã đơn": "VN55412HCM", "Người nhận": "Lê Văn E", "Địa chỉ": "670 Xô Viết Nghệ Tĩnh", "COD": "310.000đ", "Trạng thái": "⏳ Chờ điều phối"},
        {"Mã đơn": "VN77215HCM", "Người nhận": "Ngô Thị F", "Địa chỉ": "760/5 Xô Viết Nghệ Tĩnh", "COD": "0đ (Đã TT)", "Trạng thái": "⏳ Chờ điều phối"},
        {"Mã đơn": "VN20491HCM", "Người nhận": "Lê Hoàng D", "Địa chỉ": "02 Võ Oanh", "COD": "540.000đ", "Trạng thái": "⏳ Chờ điều phối"}
    ]

with st.sidebar:
    st.write("### CẤU HÌNH PHÂN TUYẾN")
    selected_hub = st.selectbox("Chọn bưu cục xuất phát:", list(VNPOST_HUBS.keys()))
    st.text_area("Địa chỉ bưu cục điều phối:", value=VNPOST_HUBS[selected_hub]["address"], height=70, disabled=True)
    st.write("---")
    stops_input = st.text_area(
        "Các điểm dừng phát hàng (1 dòng/địa chỉ):", 
        value="120 Cách Mạng Tháng Tám\n240 Điện Biên Phủ\n312 Võ Thị Sáu\n670 Xô Viết Nghệ Tĩnh\n760/5 Xô Viết Nghệ Tĩnh\n02 Võ Oanh", 
        height=150
    )
    vehicle_type = st.radio("Phương tiện vận chuyển:", ["Xe máy bưu tá chặng cuối", "Xe tải bưu chính lớn"])
    
    if st.button("TỐI ƯU LỘ TRÌNH THỰC ĐỊA"):
        st.session_state.map_ready = True
        st.session_state.lines_cache = []
        st.session_state.text_cache = []
        st.session_state.steps_cache = []

st.markdown('<p class="main-title">VIETNAM POST - ĐIỀU HÀNH LOGISTICS ĐA ĐIỂM</p>', unsafe_allow_html=True)
tab_monitor, tab_map, tab_order = st.tabs(["Trung tâm Giám sát", "Tối ưu Tuyến đường Đa điểm", "Quản lý Vận đơn"])

with tab_monitor:
    st.write(f"**Đang giám sát:** {selected_hub}")
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="metric-card"><b>ĐA GIAO POD</b><h3 style="color:#0056b3;margin:0;">1.420 kiện</h3></div>', unsafe_allow_html=True)
    c2.markdown('<div class="metric-card"><b>BƯU TÁ THỰC ĐỊA</b><h3 style="color:#0056b3;margin:0;">45 Nhân sự</h3></div>', unsafe_allow_html=True)
    c3.markdown('<div class="metric-card"><b>TỶ LỆ TOÀN TRÌNH</b><h3 style="color:#e67e22;margin:0;">94.8 %</h3></div>', unsafe_allow_html=True)
    
    st.write("---")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.write("#### 📊 Sản lượng giao thành công theo quận")
        st.bar_chart(pd.DataFrame({'Thành công': [420, 380, 290, 180, 150], 'Hoàn lại': [15, 22, 12, 8, 19]}, index=["Quận 1", "Quận 3", "Quận 5", "Quận 7", "Quận 4"]))
    with col_chart2:
        st.write("#### 📈 Trọng tải vận chuyển trong tuần (Tấn)")
        st.area_chart(pd.DataFrame({'Xe máy': [2.1, 2.8, 3.2, 2.9, 3.5, 4.1, 1.5], 'Xe tải': [8.5, 9.2, 11.0, 10.1, 12.4, 14.0, 5.0]}, index=["T2", "T3", "T4", "T5", "T6", "T7", "CN"]))

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
        addr_mapping = {0: f"Xuất phát: {selected_hub}"}
        
        step_idx = 1
        for stop_addr in raw_lines:
            for k, coords in POPULAR_STOPS.items():
                if k in stop_addr:
                    base_coords.append([coords[1], coords[0]])
                    addr_mapping[step_idx] = stop_addr.title()
                    folium.Marker([coords[0], coords[1]], tooltip=k.title(), icon=folium.Icon(color='blue')).add_to(m)
                    step_idx += 1

        if len(base_coords) > 1 and not st.session_state.lines_cache:
            coord_str = ";".join([f"{c[0]},{c[1]}" for c in base_coords])
            res = get_osrm_trip(coord_str)
            
            if res and res.get('code') == 'Ok':
                try:
                    trip_data = res['trips'][0]
                    st.session_state.lines_cache = [[p[1], p[0]] for p in trip_data['geometry']['coordinates']]
                    
                    dist_km = trip_data['distance'] / 1000
                    time_mn = trip_data['duration'] / 60
                    fuel_rate = 2.5 if "máy" in vehicle_type else 9.0
                    cost = (dist_km / 100) * fuel_rate * 23000
                    
                    st.session_state.text_cache = [f"Tổng quãng đường: {dist_km:.2f} km", f"Ước tính thời gian: {time_mn:.1f} phút", f"Chi phí nhiên liệu: {cost:.0f} VND"]
                    
                    waypoints = sorted(res.get('waypoints', []), key=lambda x: x['waypoint_index'])
                    steps_list = []
                    order_num = 1
                    for wp in waypoints:
                        w_idx = wp['waypoint_index']
                        if w_idx == 0: steps_list.append(f"🚩 {addr_mapping[w_idx]}")
                        else:
                            steps_list.append(f"➔ Chặng {order_num}: {addr_mapping[w_idx]}")
                            order_num += 1
                    st.session_state.steps_cache = steps_list
                except:
                    st.session_state.lines_cache = []

        if st.session_state.lines_cache:
            folium.PolyLine(st.session_state.lines_cache, color="#0056b3", weight=6, opacity=0.9).add_to(m)
            with col_right:
                st.write("##### THÔNG TIN LỘ TRÌNH ĐÃ TỐI ƯU")
                for txt in st.session_state.text_cache: st.info(txt)
                st.write("---")
                st.write("**📌 Thứ tự các chặng di chuyển tuần tự:**")
                for step_text in st.session_state.steps_cache: st.write(step_text)
        else:
            with col_right: st.warning("Đã ghim các tọa độ bưu cục lên hệ thống.")
    else:
        with col_right: st.info("Nhấn nút tối ưu bên trái để vẽ tuyến đường thực địa!")

    with col_left: st_folium(m, width=700, height=450, key="vnpost_map_v17_stable")

with tab_order:
    st.write("### 📦 Quản lý Trạng thái Vận đơn Thực địa")
    st.write("#### ⚙️ Cập nhật nhanh trạng thái đơn hàng")
    col_sel_order, col_sel_status, col_btn_update = st.columns([1.5, 1.5, 1])
    
    with col_sel_order:
        order_to_update = st.selectbox("Chọn mã đơn cần xử lý:", [o["Mã đơn"] for o in st.session_state.orders_db])
    with col_sel_status:
        new_status = st.selectbox("Trạng thái mới:", ["🚚 Đang giao hàng", "✅ Giao thành công", "⏳ Chờ điều phối", "❌ Khách hẹn lại"])
    with col_btn_update:
        st.write(" ")
        if st.button("XÁC NHẬN CẬP NHẬT"):
            for idx, order in enumerate(st.session_state.orders_db):
                if order["Mã đơn"] == order_to_update: st.session_state.orders_db[idx]["Trạng thái"] = new_status
            st.success(f"Đã cập nhật đơn {order_to_update} sang trạng thái mới!")
            
    st.write("---")
    st.write("#### 📊 Danh sách bưu kiện đồng bộ trực tuyến")
    st.dataframe(pd.DataFrame(st.session_state.orders_db), use_container_width=True, hide_index=True)
