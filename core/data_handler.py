import pandas as pd
import re

def mask_name(name):
    if not isinstance(name, str):
        return ""
    name_str = str(name).strip()
    if len(name_str) <= 4:
        return name_str + "***"
    return name_str[:4] + "*" * (len(name_str) - 4)

def mask_address(address):
    if pd.isna(address) or not str(address).strip():
        return ""
    address = str(address).strip()
    # Mask after Dong/Eup/Myeon/Ri/Ga
    match = re.search(r'([가-힣0-9]+(?:동|읍|면|리|가))(?:\s|$)', address)
    if match:
        end_idx = match.end(1)
        prefix = address[:end_idx]
        suffix = address[end_idx:]
        masked_suffix = "".join(['*' if not c.isspace() else c for c in suffix])
        return prefix + masked_suffix
    # Fallback masking
    parts = address.split(' ')
    if len(parts) <= 3:
        return address
    return " ".join(parts[:3]) + " *****"

def load_data(file_path_or_buffer):
    try:
        if isinstance(file_path_or_buffer, str) and file_path_or_buffer.endswith('.csv'):
            df = pd.read_csv(file_path_or_buffer, encoding='utf-8')
        elif hasattr(file_path_or_buffer, 'name') and file_path_or_buffer.name.endswith('.csv'):
            df = pd.read_csv(file_path_or_buffer, encoding='utf-8')
        else:
            df = pd.read_excel(file_path_or_buffer)
        
        # Find essential columns dynamically
        cols = df.columns.tolist()
        
        # Define mappings for common column names
        col_mappings = {
            'target_type': next((c for c in cols if '활동대상' in c), None),
            'branch': next((c for c in cols if '지사' in c), None),
            'zone': next((c for c in cols if '구역' in c or '담당자' in c), None),
            'name': next((c for c in cols if '상호' in c), None),
            'address': next((c for c in cols if '설치주소' in c or '주소' in c), None),
            'status': next((c for c in cols if '상태' in c), None),
            'processor': next((c for c in cols if '처리자' in c), None),
            'coord': next((c for c in cols if '위치좌표' in c or '위경도' in c), None),
            'lat': next((c for c in cols if '위도' in c and '위치좌표' not in c), None),
            'lng': next((c for c in cols if '경도' in c and '위치좌표' not in c), None),
            'contract_no': next((c for c in cols if '계약번호' in c), None),
            'service_no': next((c for c in cols if '서비스번호' in c), None),
            'activity_status': next((c for c in cols if '활동유무' in c), None),
            'activity_detail': next((c for c in cols if '세부 활동내역' in c or '세부활동내역' in c), None),
        }
        
        processed_data = []
        for i, row in df.iterrows():
            lat, lng = None, None
            
            # Extract from combined coord column if present
            if col_mappings['coord'] and pd.notna(row[col_mappings['coord']]):
                coord_str = str(row[col_mappings['coord']]).strip()
                if ',' in coord_str:
                    try:
                        parts = coord_str.split(',')
                        lat = float(parts[0].strip())
                        lng = float(parts[1].strip())
                    except:
                        pass
            
            # Fallback to separate lat/lng columns
            if lat is None and col_mappings['lat'] and pd.notna(row[col_mappings['lat']]):
                lat = row[col_mappings['lat']]
            if lng is None and col_mappings['lng'] and pd.notna(row[col_mappings['lng']]):
                lng = row[col_mappings['lng']]
            
            # Require lat/lng for mapping
            if not lat or not lng:
                continue
                
            def safe_format(val):
                if pd.isna(val) or str(val).strip() == '':
                    return '-'
                val_str = str(val).strip()
                if val_str.endswith('.0'):
                    return val_str[:-2]
                return val_str

            item = {
                'target_type': str(row[col_mappings['target_type']]).strip() if col_mappings['target_type'] and pd.notna(row[col_mappings['target_type']]) else '기타',
                'branch': str(row[col_mappings['branch']]).strip() if col_mappings['branch'] and pd.notna(row[col_mappings['branch']]) else '미지정',
                'zone': str(row[col_mappings['zone']]).strip() if col_mappings['zone'] and pd.notna(row[col_mappings['zone']]) else '미지정',
                'name': mask_name(row[col_mappings['name']]) if col_mappings['name'] else '',
                'address': mask_address(row[col_mappings['address']]) if col_mappings['address'] else '',
                'status': str(row[col_mappings['status']]).strip() if col_mappings['status'] and pd.notna(row[col_mappings['status']]) else '미접수',
                'processor': str(row[col_mappings['processor']]).strip() if col_mappings['processor'] and pd.notna(row[col_mappings['processor']]) else '-',
                'lat': float(lat),
                'lng': float(lng),
                'contract_no': safe_format(row[col_mappings['contract_no']]) if col_mappings['contract_no'] else '-',
                'service_no': safe_format(row[col_mappings['service_no']]) if col_mappings['service_no'] else '-',
                'activity_status': str(row[col_mappings['activity_status']]).strip() if col_mappings['activity_status'] and pd.notna(row[col_mappings['activity_status']]) else '미접수',
                'activity_detail': str(row[col_mappings['activity_detail']]).strip() if col_mappings['activity_detail'] and pd.notna(row[col_mappings['activity_detail']]) else '-'
            }
            # Normalize activity status
            if item['activity_status'].lower() in ['x', '미접수', '-', '']:
                item['activity_status'] = '미접수'
            processed_data.append(item)
            
        return pd.DataFrame(processed_data)
    
    except Exception as e:
        return str(e)
