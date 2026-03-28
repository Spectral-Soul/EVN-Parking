from datetime import datetime

# Base rates
RATE_NON_EV = 20
RATE_EV = 30
PEAK_RATE = 50
NIGHT_RATE = 10

def calculate_price(is_ev, start_time, end_time):
    if not start_time or not end_time:
        return 0

    if isinstance(start_time, str):
        # basic parsing
        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    # Calculate duration in hours
    diff = end_time - start_time
    hours = diff.total_seconds() / 3600

    # Dynamic pricing based on start time hour
    hour = start_time.hour
    
    # Night: 10 PM (22) to 6 AM (6)
    if hour >= 22 or hour < 6:
        base = NIGHT_RATE
    # Peak: 9 AM (9) to 11 AM (11), and 5 PM (17) to 8 PM (20)
    elif (9 <= hour < 11) or (17 <= hour < 20):
        base = PEAK_RATE
    else:
        base = RATE_EV if is_ev else RATE_NON_EV

    # Add flat sum for the hours 
    return max(10, round(base * hours, 2)) # minimum 10 INR
