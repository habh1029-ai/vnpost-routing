import streamlit as st
import folium
import math
import requests
import pandas as pd
from streamlit_folium import folium_static

# 1. CAU HINH GIAO DIEN WEB
st.set_page_config(
    page_title="VNPOST Multi-drop Routing", 
    layout="wide"
)

# 2. CHEN CSS CUSTOM
st.markdown("""
    <style>
        .main-title {
            font-size: 2rem !important;
            font-weight: 800;
            color: #0056b3;
            text-transform: uppercase;
            border-bottom: 4px solid #F2A900;
            padding-bottom: 10px;
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

# 3. CO SO DU LIEU BUU CUC
VNPOST_HUBS = {
    "Buu cuc Tan Dinh (Q1)": "230 Hai Ba Trung, Quan 1",
    "Buu cuc Giao dich Sai Gon (Q1)": "2 Cong xa Paris, Quan 1",
    "Buu cuc Quan 3": "2Bis Ba Huyen Thanh Quan, Quan 3",
    "Buu cuc Ban Co (Q3)": "49A Cao Thang, Quan 3",
    "Buu cuc Quan 5": "26 Nguyen Thi, Quan 5",
    "Buu cuc Quan 7": "1441 Huynh Tan Phat, Quan 7"
}

# 4. MOCK DATA BIEU DO
DISTRICT_DATA = {
    "Thanh cong": [420, 380, 290, 180, 150],
    "Hoan lai": [15, 22, 12, 8, 19]
}
DISTRICT_INDEX = ["Quan 1", "Quan 3", "Quan 5", "Quan 7", "Quan 4"]

WEIGHT_DATA = {
    "Xe may": [2.1, 2.8, 3.2, 2.9, 3.5, 4.1, 1.5],
    "Xe tai": [8.5, 9.2, 11.0, 10.1, 12.4, 14.0, 5.0]
}
WEIGHT_INDEX = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

MOCK_ORDERS = {
    "Ma Van Don": ["VN94827HCM", "VN10482HCM", "VN58291HCM"],
    "Nguoi Nhan": ["Nguyen Van A", "Tran Thi B", "Le Hoang C"],
    "Dia Chi": ["100 Cao Thang, Q3", "320 Nguyen Du, Q1", "Ho Con Rua, Q3"],
    "Loai Hang": ["Tai lieu", "Dien tu", "Buu kien"]
}

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

# 5. SIDEBAR DIEU HUONG
with st.sidebar:
    st.write("### CAU HINH PHAN TUYEN")
    selected_start_hub = st.selectbox("Chon buu cuc xuat phat:", list(VNPOST_HUBS.keys()))
    start_input = st.text_area("Dia chi buu cuc:", value=VNPOST_HUBS[selected_start_hub], height=70)
    
    st.write("---")
    st.write("Danh sach cac diem giao hang:")
    st.caption("Nhap moi dia chi tren 1 dong chuoi:")
    
    default_stops = "100 Cao Thang, Quan 3\n320 Nguyen Du, Quan 1\nHo Con Rua, Quan 3"
    stops_input = st.text_area("Cac diem dung chan:", value=default_stops, height=120)
    
    vehicle_type = st.radio("Phuong tien:", ["Xe may chang cuoi", "Xe tai lon"])
    activated = st.button("TOI UU HOA LO TRINH")

# 6. HIEU UNG TIEU DE TRANG CHINH
st.markdown('<p class="main-title">VIETNAM POST - DIEU HANH LOGISTICS DA DIEM</p>', unsafe_allow_html=True)

tab_monitor, tab_map, tab_order = st.tabs([
    "Trung tam Giam sat", 
    "Toi uu Tuyen duong", 
    "Quan ly Van don"
])

# TAB 1: GIAM SAT
with tab_monitor:
    st.write(f"**Dang giam sat:** {selected_start_hub}")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown('<div class="metric-card"><p>DA GIAO</p><h3>1,420 kien</h3></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown('<div class="metric-card"><p>BUU TA</p><h3>45 Nhan su</h3></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown('<div class="metric-card"><p>TY LE POD</p><h3>94.8 %</h3></div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.bar_chart(pd.DataFrame(DISTRICT_DATA, index=DISTRICT_INDEX))
    with col_c2:
        st.area_chart(pd.DataFrame(WEIGHT_DATA, index=WEIGHT_INDEX))

# TAB 2: TOI UU BAN DO DA DIEM
with tab_map:
    st.write("### So do dinh tuyen chuoi diem dung cho tai xe")
    col_left, col_right = st.columns([1.8, 1.2])
    
    m = folium.Map(location=[10.7760, 106.7032], zoom_start=13)

    if activated:
        raw_stops = [line.strip() for line in stops_input.split('\n') if line.strip()]
        if start_input.strip() and raw_stops:
            try:
                start_loc = get_coordinates_from_address(start_input)
                if start_loc:
                    all_coordinates = [[start_loc['lat'], start_loc['lon']]]
                    valid_names = ["Buu cuc xuat phat"]
                    
                    for idx, stop_addr in enumerate(raw_stops, 1):
                        loc = get_coordinates_from_address(stop_addr)
                        if loc:
                            all_coordinates.append([loc['lat'], loc['lon']])
                            valid_names.append(f"Diem {idx}: {stop_addr}")
                    
                    if len(all_coordinates) >= 2:
                        total_dist = 0.0
                        total_time = 0.0
                        m = folium.Map(location=all_coordinates[0], zoom_start=14)
                        
                        folium.Marker(all_coordinates[0], tooltip="XUAT PHAT", icon=folium.Icon(color='green')).add_to(m)
                        
                        for i in range(len(all_coordinates) - 1):
                            p_start = all_coordinates[i]
                            p_end = all_coordinates[i+1]
                            
                            folium.Marker(p_end, tooltip=valid_names[i+1], icon=folium.Icon(color='blue')).add_to(m)
                            
                            url = f"http://router.project-osrm.org/route/v1/driving/{p_start[1]},{p_start[0]};{p_end[1]},{p_end[0]}?overview=full&geometries=geojson"
                            res = requests.get(url).json()
                            
                            if res.get('code') == 'Ok':
                                chunk = res['routes'][0]
                                gps_coords = [[c[1], c[0]] for c in chunk['geometry']['coordinates']]
                                total_dist += chunk['distance'] / 1000
                                total_time += chunk['duration'] / 60
                                folium.PolyLine(gps_coords, color="#0056b3", weight=5).add_to(m)
                        
                        fuel_rate = 2.5 if "may" in vehicle_type else 9.0
                        fuel_cost = (total_dist / 100) * fuel_rate * 23000
                        
                        with col_left:
                            folium_static(m, width=700, height=450)
                        with col_right:
                            st.write("##### THONG TIN HANH TRINH")
                            st.info(f"Quang duong: {total_dist:.2f} km\n\nThoi gian: {total_time:.1f} phut\n\nChi phi: {fuel_cost:.0f} VND")
                            st.write("---")
                            st.write("**Thu tu phan phat:**")
                            for name in valid_names:
                                st.write(f"- {name}")
            except Exception as e:
                st.error(f"Loi ban do: {e}")
        else:
            with col_left:
                folium_static(m, width=700, height=450)
    else:
        with col_left:
            folium_static(m, width=700, height=450)

# TAB 3: VAN DON
with tab_order:
    st.write("### Danh sach kiem soat van don")
    st.dataframe(pd.DataFrame(MOCK_ORDERS), use_container_width=True)
