import re

def classify_location(location_str: str) -> str:
    """
    Classify a location string into one of:
    - BANGALORE
    - HYDERABAD
    - REMOTE_INDIA
    - OTHER_INDIA
    - GLOBAL
    """
    if not location_str:
        return "GLOBAL"
    
    loc_lower = location_str.lower()
    
    # Exclude patterns representing non-India locations
    exclude_patterns = [
        r'\b(united states|us|usa|europe|singapore|uk|united kingdom|australia|germany|canada|london|sf|san francisco|ny|new york|berlin|tokyo|france|spain|italy|ireland|netherlands|sweden|switzerland|poland|finland|norway|denmark|japan|china|sydney|melbourne|singapore)\b'
    ]
    
    is_exclude = False
    for pattern in exclude_patterns:
        if re.search(pattern, loc_lower):
            is_exclude = True
            break
            
    # Priority checks: Bangalore / Bengaluru
    if 'bangalore' in loc_lower or 'bengaluru' in loc_lower:
        return "BANGALORE"
        
    # Priority checks: Hyderabad
    if 'hyderabad' in loc_lower:
        return "HYDERABAD"
        
    # Remote India: requires both 'remote' and 'india'
    if 'remote' in loc_lower and 'india' in loc_lower:
        return "REMOTE_INDIA"
        
    # If it matched exclude list, classify as GLOBAL
    if is_exclude:
        return "GLOBAL"
        
    # Mentions India but not Bangalore/Hyderabad/Remote India
    if 'india' in loc_lower:
        return "OTHER_INDIA"
        
    # Default is GLOBAL
    return "GLOBAL"
