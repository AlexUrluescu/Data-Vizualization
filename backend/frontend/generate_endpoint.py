import datetime

DEVICE_ID = "1600013B"
SENSOR = "all"

START_DATE_STR = "2026-03-01 00:00:00" 
END_DATE_STR = "2026-03-06 23:59:59"


def generate_uradmonitor_url(device_id, sensor, start_str, end_str):
    date_format = "%Y-%m-%d %H:%M:%S"
    
    start_date = datetime.datetime.strptime(start_str, date_format)
    end_date = datetime.datetime.strptime(end_str, date_format)
    
    now = datetime.datetime.now()
    
    start_interval = max(0, int((now - start_date).total_seconds()))
    stop_interval = max(0, int((now - end_date).total_seconds()))
    

    url = f"http://data.uradmonitor.com/api/v1/devices/{device_id}/{sensor}/{start_interval}/{stop_interval}"
    
    return url, start_interval, stop_interval

try:
    final_url, start_sec, stop_sec = generate_uradmonitor_url(
        DEVICE_ID, SENSOR, START_DATE_STR, END_DATE_STR
    )
    
    print("--- uRADMonitor URL Generator ---")
    print(f"Target Start : {START_DATE_STR} ({start_sec} seconds ago)")
    print(f"Target End   : {END_DATE_STR} ({stop_sec} seconds ago)")
    print("-" * 33)
    print(f"Generated URL:\n{final_url}")

except ValueError as e:
    print(f"Error: Please check your date formatting. It must be YYYY-MM-DD HH:MM:SS. ({e})")