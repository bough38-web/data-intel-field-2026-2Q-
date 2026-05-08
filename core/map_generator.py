import folium
from folium.plugins import MarkerCluster, LocateControl
import math

def create_map(df, tiles='OpenStreetMap'):
    # Initialize map
    if df.empty:
        # Default center of Korea if empty
        m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles=tiles)
        return m
    
    # Center map around the average of provided coordinates
    center_lat = df['lat'].mean()
    center_lng = df['lng'].mean()
    m = folium.Map(location=[center_lat, center_lng], zoom_start=11, tiles=tiles)
    
    LocateControl(
        auto_start=False, 
        strings={"title": "내 위치 보기"},
        flyTo=True,
        drawCircle=True,
        locateOptions={
            'maxZoom': 16,
            'enableHighAccuracy': True,
            'timeout': 10000,
            'maximumAge': 0
        }
    ).add_to(m)

    # Add marker cluster
    marker_cluster = MarkerCluster().add_to(m)
    
    for _, row in df.iterrows():
        # Premium Glowing Dot Icon based on target type
        color = '#ef4444' if row['target_type'] == 'SP' else '#f59e0b' if row['target_type'] == 'SG' else '#3b82f6'
        
        html_icon = f'''
            <div style="background-color: {color}; border-radius: 50%; width: 14px; height: 14px; border: 2px solid white; box-shadow: 0 0 10px {color};"></div>
        '''
        icon = folium.DivIcon(html=html_icon, icon_anchor=(7, 7))
        
        # Build Popup HTML
        popup_html = f"""
        <div style="font-family: 'Pretendard', sans-serif; width: 220px; padding: 5px;">
            <div style="border-bottom: 2px solid #2563eb; padding-bottom: 5px; margin-bottom: 8px;">
                <h4 style="margin: 0; color: #0f172a; font-size: 14px; font-weight: 800;">
                    {row['name']}
                </h4>
                <span style="font-size: 11px; background-color: #e2e8f0; padding: 2px 6px; border-radius: 4px; color: #475569; font-weight: bold;">
                    {row['target_type']}
                </span>
            </div>
            <div style="font-size: 12px; color: #334155; line-height: 1.6;">
                <p style="margin: 3px 0;"><b>계약번호:</b> {row.get('contract_no', '-')}</p>
                <p style="margin: 3px 0;"><b>서비스번호:</b> {row.get('service_no', '-')}</p>
                <p style="margin: 3px 0;"><b>지사:</b> {row['branch']}</p>
                <p style="margin: 3px 0;"><b>구역:</b> {row['zone']}</p>
                <p style="margin: 3px 0;"><b>상태:</b> <span style="color: {'red' if row['status']=='미접수' else 'green'}; font-weight: bold;">{row['status']}</span></p>
                <p style="margin: 3px 0;"><b>처리자:</b> {row['processor']}</p>
                <div style="margin-top: 8px; padding: 6px; background-color: #f8fafc; border-radius: 4px; font-size: 11px; color: #64748b; border: 1px solid #e2e8f0;">
                    {row['address']}
                </div>
            </div>
        </div>
        """
        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=row['name'],
            icon=icon
        ).add_to(marker_cluster)
        
    return m

def get_distance(lat1, lng1, lat2, lng2):
    return math.sqrt((lat1 - lat2)**2 + (lng1 - lng2)**2)

def create_route_map(df, start_index=0, max_stops=10, tiles='OpenStreetMap'):
    if df.empty:
        return create_map(df, tiles=tiles)
        
    # Start coordinates (usually the first item in the filtered df)
    start_row = df.iloc[start_index]
    c_lat, c_lng = start_row['lat'], start_row['lng']
    
    # Initialize Map
    m = folium.Map(location=[c_lat, c_lng], zoom_start=13, tiles=tiles)
    
    LocateControl(
        auto_start=False, 
        strings={"title": "내 위치 보기"},
        flyTo=True,
        drawCircle=True,
        locateOptions={
            'maxZoom': 16,
            'enableHighAccuracy': True,
            'timeout': 10000,
            'maximumAge': 0
        }
    ).add_to(m)
    
    unvisited = df.to_dict('records')
    route = []
    
    # Remove start node from unvisited and add to route
    start_node = unvisited.pop(start_index)
    start_node['distFromPrev'] = 0
    route.append(start_node)
    
    total_dist_km = 0
    
    for _ in range(min(max_stops - 1, len(unvisited))):
        nearest_idx = -1
        min_d = float('inf')
        nearest = None
        
        for idx, t in enumerate(unvisited):
            d = get_distance(c_lat, c_lng, t['lat'], t['lng'])
            if d < min_d:
                min_d = d
                nearest_idx = idx
                nearest = t
                
        if nearest:
            km = min_d * 111  # approximate degree to km
            total_dist_km += km
            nearest['distFromPrev'] = km
            route.append(nearest)
            unvisited.pop(nearest_idx)
            c_lat = nearest['lat']
            c_lng = nearest['lng']
            
    # Draw thin, elegant PolyLine
    route_coords = [[r['lat'], r['lng']] for r in route]
    folium.PolyLine(
        route_coords, 
        color="#38bdf8", 
        weight=2.5, 
        opacity=0.8,
        dash_array='5, 5'
    ).add_to(m)
    
    # Add Markers and Distance Labels for Route
    for i in range(len(route)):
        r = route[i]
        is_start = (i == 0)
        color = '#3b82f6' if is_start else '#ef4444'
        
        # Add midpoint distance label for all except first
        if i > 0:
            prev_r = route[i-1]
            mid_lat = (prev_r['lat'] + r['lat']) / 2
            mid_lng = (prev_r['lng'] + r['lng']) / 2
            
            dist_km = r['distFromPrev']
            if dist_km < 1.0:
                dist_str = f"{dist_km*1000:.0f}m"
            else:
                dist_str = f"{dist_km:.1f}km"
                
            dist_icon = f'''
                <div style="background-color: rgba(15, 23, 42, 0.85); border: 1px solid #38bdf8; border-radius: 12px; padding: 2px 8px; font-size: 11px; font-weight: bold; color: #38bdf8; white-space: nowrap; box-shadow: 0 2px 5px rgba(0,0,0,0.4); transform: translate(-50%, -50%); display: inline-block; backdrop-filter: blur(4px);">
                    {dist_str}
                </div>
            '''
            folium.Marker(
                location=[mid_lat, mid_lng],
                icon=folium.DivIcon(html=dist_icon, icon_size=(0,0))
            ).add_to(m)
        
        # Build Popup HTML
        popup_html = f"""
        <div style="font-family: 'Pretendard', sans-serif; width: 220px; padding: 5px;">
            <div style="border-bottom: 2px solid #2563eb; padding-bottom: 5px; margin-bottom: 8px;">
                <h4 style="margin: 0; color: #0f172a; font-size: 14px; font-weight: 800;">
                    [{i+1}번 방문] {r['name']}
                </h4>
                <span style="font-size: 11px; background-color: #e2e8f0; padding: 2px 6px; border-radius: 4px; color: #475569; font-weight: bold;">
                    {r['target_type']}
                </span>
            </div>
            <div style="font-size: 12px; color: #334155; line-height: 1.6;">
                <p style="margin: 3px 0;"><b>계약번호:</b> {r.get('contract_no', '-')}</p>
                <p style="margin: 3px 0;"><b>서비스번호:</b> {r.get('service_no', '-')}</p>
                <p style="margin: 3px 0;"><b>상태:</b> {r['status']}</p>
                <p style="margin: 3px 0; color: #f97316; font-weight: bold;"><b>이전 지점으로부터:</b> {r['distFromPrev']*1000:.0f}m</p>
            </div>
        </div>
        """
        
        marker_text = '출발' if is_start else str(i+1)
        
        # Use DivIcon for numbered markers
        html_icon = f'''
            <div style="background-color: {color}; color: white; border-radius: 50%; width: 26px; height: 26px; display: flex; justify-content: center; align-items: center; font-size: 12px; font-weight: 800; border: 2px solid rgba(255,255,255,0.9); box-shadow: 0 0 12px {color};">
                {marker_text}
            </div>
        '''
        
        folium.Marker(
            location=[r['lat'], r['lng']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{i+1}번째: {r['name']}",
            icon=folium.DivIcon(html=html_icon, icon_anchor=(13, 13))
        ).add_to(m)
        
    return m, total_dist_km

def export_map_to_html(m, filename="map_export.html"):
    # Saves map to HTML string or file
    html_data = m._repr_html_()
    return html_data
