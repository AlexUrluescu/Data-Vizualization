import panel as pn
import folium
import altair as alt
import pandas as pd
import datetime as dt
import random
import threading
import numpy as np
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
USER_ID = os.getenv("USER_ID")
USER_HASH = os.getenv("USER_HASH")

metadata_senzori = [
    {"id": "1600013B", "name": "Sibiu 1", "lat": 45.7982683, "lon": 24.1488102},
    {"id": "1600019F", "name": "Sibiu 2", "lat": 45.807144, "lon": 24.145801},
    {"id": "16000284", "name": "Sibiu 3", "lat": 45.786566, "lon": 24.16383},
    {"id": "16000224", "name": "Sibiu 4", "lat": 45.80865637, "lon": 24.14074895},
    {"id": "16000341", "name": "Vestem", "lat": 45.7163527, "lon": 24.23857099},
    {"id": "16000342", "name": "Selimbar", "lat": 45.76698129, "lon": 24.19551811},
    {"id": "16000343", "name": "Sibiu 5", "lat": 45.810222, "lon": 24.179481},
    {"id": "16000344", "name": "Mohu", "lat": 45.7429537, "lon": 24.2231919},
    {"id": "8200029B", "name": "Sibiu 6", "lat": 45.793112, "lon": 24.152697},
]

current_state = {s['id']: {"value": 0.0, "status": "Activ"} for s in metadata_senzori}


def generate_mock_history():
    end_date = pd.Timestamp.now().floor('h') 
    
    start_date = end_date - pd.Timedelta(days=7)

    time_range = pd.date_range(start=start_date, end=end_date, freq='h') 
    
    history_data = []

    print("Generating mock history data...")
    
    for t in time_range:
        for s in metadata_senzori:
            base_temp = 15 + 10 * np.sin((t.hour - 6) * np.pi / 12) 
            noise = random.uniform(-2, 2)
            val = base_temp + noise
            
            status = "Activ"
            if val > 30: status = "Alertă"
            if random.random() < 0.05: status = "Inactiv"
            
            history_data.append({
                "timestamp": t,
                "sensor_id": s['id'],
                "value": val,
                "status": status
            })
            
    return pd.DataFrame(history_data)

df_history = generate_mock_history()

print("Mock history data generated with", len(df_history), "records.")

def render_dashboard_page():
    pn.extension('vega')
    
    # --- WIDGETS ---
    mode_switch = pn.widgets.Switch(name='Live Mode', value=True)
    mode_label = pn.widgets.StaticText(value='<b>Live Mode</b> (Oprește pentru istoric)')
    
    datetime_picker = pn.widgets.DatetimePicker(
        name='Selectează Ora', 
        value=dt.datetime.now() - dt.timedelta(hours=2),
        disabled=True
    )
    
    counter = pn.widgets.IntInput(value=0, visible=False)

    @pn.depends(mode_switch.param.value, watch=True)

    def fetch_data_from_api():
        if not mode_switch.value:
            return

        try:
            api_headers = {
                "X-User-id": USER_ID,
                "X-User-hash": USER_HASH               
            }
            
            response = requests.get(API_URL, headers=api_headers, timeout=3)
            
            if response.status_code == 200:
                api_data = response.json() 
                
                for item in api_data:
                    api_id = item.get("id")         
                    temp_value = item.get("last_temperature")

                    if api_id in current_state:
                        
                
                        if temp_value is not None:
                            current_state[api_id]["value"] = float(temp_value)
                            
                            if float(temp_value) == 0:
                                current_state[api_id]["status"] = "Inactiv"
                            elif float(temp_value) > 30:
                                current_state[api_id]["status"] = "Alertă"
                            else:
                                current_state[api_id]["status"] = "Activ"
                
           
                counter.value += 1
                
            else:
                print(f"API Error: Status {response.status_code}")

        except Exception as e:
            print(f"Error fetching data: {e}")

   
    pn.state.add_periodic_callback(fetch_data_from_api, period=300000)
    pn.state.onload(fetch_data_from_api)

    @pn.depends(counter.param.value, mode_switch.param.value, datetime_picker.param.value)
    def get_map(tick, is_live, selected_time):
        
        m = folium.Map(location=[45.7983, 24.1256], zoom_start=13)
        
        for senzor_meta in metadata_senzori:
            s_id = senzor_meta['id']
            
            valoare = 0.0
            status = "N/A"
            timestamp_str = "Acum"

            if is_live:
                data = current_state[s_id]
                valoare = data['value']
                status = data['status']
            
            else:
        
                target_hour = pd.Timestamp(selected_time).floor('h')
                
                record = df_history[
                    (df_history['sensor_id'] == s_id) & 
                    (df_history['timestamp'] == target_hour)
                ]

                print(record)
                
                if not record.empty:
                    valoare = record.iloc[0]['value']
                    status = record.iloc[0]['status']
                    timestamp_str = target_hour.strftime('%d-%m %H:%M')
                else:
                    status = "Fără Date"

            color = 'green'
            if status == 'Inactiv' or status == 'Fără Date': color = 'gray'
            elif status == 'Alertă': color = 'red'

            popup_content = f"""
                <div style='min-width: 140px'>
                    <b>{senzor_meta['name']}</b><br>
                    <small>Data: {timestamp_str}</small><hr style="margin:5px 0">
                    Status: <b>{status}</b><br>
                    Temp: <b>{valoare:.1f} °C</b>
                </div>
            """

            folium.Marker(
                location=[senzor_meta['lat'], senzor_meta['lon']],
                popup=popup_content,
                tooltip=f"{senzor_meta['name']} ({valoare:.1f}°C)",
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)

        return pn.pane.plot.Folium(m, height=400)

   
    control_row = pn.Row(
        pn.Column(mode_label, mode_switch),
        datetime_picker
    )
    
    layout = pn.Column(
        control_row,
        counter,
        get_map,
        pn.layout.Divider(),
    )

    return layout

def render_admin_page():
    pn.extension('tabulator')

    upload_widget = pn.widgets.FileInput(accept='.xlsx', name='Upload Excel')
    admin_btn = pn.widgets.Button(name='Go to Dashboard', button_type='primary', width=100)
    admin_btn.js_on_click(code="window.location.href = '/'")

    @pn.depends(upload_widget.param.value)
    def process_excel(file_content):
        if file_content is None:
            return pn.pane.Markdown("### 📂 Please upload an Excel file to see the data.")
        
        try:
            df = pd.read_excel(io.BytesIO(file_content))

            print("\n" + "="*40)
            print("🚗 CAR STATISTICS REPORT")
            print("="*40)

            for index, row in df.iterrows():
                city_name = row.iloc[0] 
                print(f"\n🏙️  City: {city_name}")
                
                for year_column in df.columns[1:]:
                    car_count = row[year_column]
                    print(f"   📅 Year {year_column}: {car_count} cars")

            print("\n" + "="*40 + "\n")

            return pn.widgets.Tabulator(df, pagination='remote', page_size=10, height=400)
            
        except Exception as e:
            print(f"Error: {e}")
            return pn.pane.Alert(f"Error reading file: {str(e)}", alert_type='danger')
        

    layout = pn.Column(
        admin_btn,
        upload_widget,
        pn.layout.Divider(),
        process_excel
    )

    return layout   


def run_panel_server():
    pn.serve(
        {'/dashboard': render_dashboard_page, '/admin': render_admin_page}, 
        port=5006, 
        allow_websocket_origin=["127.0.0.1:5000", "127.0.0.1:5001"], 
        show=False,
        loop=None
    )

t = threading.Thread(target=run_panel_server, daemon=True)
t.start()