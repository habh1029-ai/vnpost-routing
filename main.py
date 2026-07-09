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


#