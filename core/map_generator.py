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
    
    # Custom Tiles Logic with prefer_canvas=True for speed
    if tiles == 'Vworld':
        m = folium.Map(location=[center_lat, center_lng], zoom_start=11, tiles=None, prefer_canvas=True)
        # Use Google Maps Street for "Naver-like" premium detail and high stability
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google 상세지도',
            overlay=False,
            control=True
        ).add_to(m)
    elif tiles == 'GoogleHybrid':
        m = folium.Map(location=[center_lat, center_lng], zoom_start=11, tiles=None, prefer_canvas=True)
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google 위성',
            overlay=False,
            control=True
        ).add_to(m)
    else:
        m = folium.Map(location=[center_lat, center_lng], zoom_start=11, tiles=tiles, prefer_canvas=True)
    
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

    # Add marker cluster with extreme performance optimization
    marker_cluster = MarkerCluster(
        disableClusteringAtZoom=17,
        spiderfyOnMaxZoom=True,
        showCoverageOnHover=False,
        zoomToBoundsOnClick=True,
        animate=False,
        chunkedLoading=True, # Load markers in chunks for UI responsiveness
        removeOutsideVisibleBounds=True # Only render what's on screen
    ).add_to(m)
    
    for _, row in df.iterrows():
        # Premium Colors
        status_color = '#10b981' if row['activity_status'] != '미접수' else '#ef4444'
        type_color = '#ef4444' if row['target_type'] == 'SP' else '#f59e0b' if row['target_type'] == 'SG' else '#3b82f6'
        
        current_status = str(row.get('status', ''))
        is_renewal = '재계약' in current_status
        is_visit = '방문상담' in current_status
        
        if is_renewal:
            marker_border = '#a855f7' # Purple
            box_shadow = f'0 0 12px {marker_border}, 0 0 0 3px rgba(168,85,247,0.4)'
            status_badge = '<span style="font-size: 10px; font-weight: 800; background: #a855f7; padding: 2px 6px; border-radius: 4px; color: white; margin-left: 4px;">🌟 재계약</span>'
        elif is_visit:
            marker_border = '#0ea5e9' # Sky blue
            box_shadow = f'0 0 12px {marker_border}, 0 0 0 3px rgba(14,165,233,0.4)'
            status_badge = '<span style="font-size: 10px; font-weight: 800; background: #0ea5e9; padding: 2px 6px; border-radius: 4px; color: white; margin-left: 4px;">💬 방문상담</span>'
        else:
            marker_border = '#ffffff'
            box_shadow = f'0 0 8px {type_color}, 0 0 0 2px rgba(255,255,255,0.3)'
            status_badge = ''
            
        # Enhanced Marker Icon: Glow effect + Clear border
        html_icon = f'''
            <div style="
                background-color: {type_color}; 
                border-radius: 50%; 
                width: 14px; 
                height: 14px; 
                border: 2px solid {marker_border};
                box-shadow: {box_shadow};
            "></div>
        '''
        icon = folium.DivIcon(html=html_icon, icon_anchor=(7, 7))
        
        # Build Premium Popup HTML (Dark Theme matching Data Intel PRO)
        popup_html = f"""
        <div style="font-family: 'Pretendard', sans-serif; width: 240px; padding: 0; background: #0f172a; border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1);">
            <div style="background: linear-gradient(135deg, {type_color}dd, {type_color}); padding: 12px; color: white;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <div>
                        <span style="font-size: 10px; font-weight: 800; background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">{row['target_type']}</span>
                        {status_badge}
                    </div>
                    <span style="font-size: 10px; font-weight: 600; color: white;">{row['branch']} 지사</span>
                </div>
                <h4 style="margin: 0; font-size: 15px; font-weight: 800; letter-spacing: -0.02em;">{row['name']}</h4>
            </div>
            <div style="padding: 12px; background: #0f172a; color: #f8fafc;">
                <div style="margin-bottom: 8px;">
                    <p style="margin: 2px 0; font-size: 11px; color: #94a3b8;">서비스번호: <span style="color: #f1f5f9;">{row.get('service_no', '-')}</span></p>
                    <p style="margin: 2px 0; font-size: 11px; color: #94a3b8;">구역: <span style="color: #f1f5f9;">{row['zone']}</span></p>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                    <span style="font-size: 12px; font-weight: 700; color: {status_color};">{row['activity_status']}</span>
                    <span style="font-size: 10px; color: #64748b;">{row['processor']}</span>
                </div>
                <div style="margin-top: 10px; font-size: 11px; line-height: 1.4; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                    📍 {row['address']}
                </div>
            </div>
        </div>
        """
        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=folium.Tooltip(f"[{row['target_type']}] {row['name']}", permanent=False),
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
    
    # Initialize Map with Custom Tiles Logic (Speed optimized)
    if tiles == 'Vworld':
        m = folium.Map(location=[c_lat, c_lng], zoom_start=13, tiles=None, prefer_canvas=True)
        # Use Google Maps Street for "Naver-like" premium detail and high stability
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google 상세지도',
            overlay=False,
            control=True
        ).add_to(m)
    elif tiles == 'GoogleHybrid':
        m = folium.Map(location=[c_lat, c_lng], zoom_start=13, tiles=None, prefer_canvas=True)
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google 위성',
            overlay=False,
            control=True
        ).add_to(m)
    else:
        m = folium.Map(location=[c_lat, c_lng], zoom_start=13, tiles=tiles, prefer_canvas=True)
    
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
