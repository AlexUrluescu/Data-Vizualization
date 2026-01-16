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
import json

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

current_state = {s['id']: {"temp": 0.0, "status": "Activ", "humidity": 0.0, "carbon": 0.0} for s in metadata_senzori}


def get_api_intervals(date_range_tuple):
    if not date_range_tuple or len(date_range_tuple) != 2:
        return None, None

    start_date, end_date = date_range_tuple
    now = dt.datetime.now()

    if isinstance(start_date, dt.date) and not isinstance(start_date, dt.datetime):
        start_date = dt.datetime.combine(start_date, dt.time.min)
    if isinstance(end_date, dt.date) and not isinstance(end_date, dt.datetime):
        end_date = dt.datetime.combine(end_date, dt.time.max)

    start_seconds = int((now - start_date).total_seconds())
    stop_seconds = int((now - end_date).total_seconds())

    return max(0, start_seconds), max(0, stop_seconds)

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

df_api_data = pd.DataFrame()

def getDeviceIdsFromSelections(location_selector):
        selected_id = ''
        if location_selector == 'Terezian':
            selected_id = "1600019F"
        if location_selector == 'Tiglari':
            selected_id = "16000224"
        if location_selector == 'Centru':
            selected_id = "1600013B"
        if location_selector == 'Caposu':
            selected_id = "16000284"
        if location_selector == 'Vasile Aron':
            selected_id = "16000343"
        if location_selector == 'Gusterita':
            selected_id = "16000284"
        if location_selector == 'Selimbar':
            selected_id = "16000342"
        return selected_id
    

def getParameter(parameter_selector):
        data = {
            "parameter": "",
            "title": "",
            "subtitle": "",
            "color": ""
        }

        if parameter_selector == 'Temperature':
            data["parameter"] = "temperature"
            data["color"] = "#FF5733"
            data["title"]="Temperature History"
            data["subtitle"] = "Temperature (°C)"

        if parameter_selector == 'Humidity':
            data["parameter"] = "humidity"
            data["color"] = "#0095F9"
            data["title"]="Humidity History"
            data["subtitle"] = "Humidity %"

        if parameter_selector == 'Carbon Monoxide':
            data["parameter"] = "pm25"
            data["color"] = "#595959"
            data["title"]="Monoxid Carbon History"
            data["subtitle"] = "Monoxid Carbon"
        
        return data

def get_temperature_plot(parameter_selector):
    if df_api_data.empty:
        return pn.pane.Markdown("### Waiting for data...")
    
    print(f"parameter_selector: {parameter_selector}")
    parameter_data = getParameter(parameter_selector)

    chart = alt.Chart(df_api_data).mark_line(point=True).encode(
        x=alt.X('timestamp:T', title='Time', axis=alt.Axis(format='%H:%M')),
        y=alt.Y(f'{parameter_data["parameter"]}:Q', title=f'{parameter_data["subtitle"]}'),
        tooltip=[
            alt.Tooltip('timestamp:T', format='%Y-%m-%d %H:%M'), 
            'temperature', 
            'humidity', 
            'pm25'
        ],
        color=alt.value(parameter_data["color"]) 
    ).properties(
        title=parameter_data["title"],
        height=300,
        width='container' 
    ).interactive()

    return pn.pane.Vega(chart, sizing_mode='stretch_width')

def render_dashboard_page():
    pn.extension('vega')
    
    # --- WIDGETS ---
    checkbox = pn.widgets.Checkbox(name='All', value=True)
    checkboxTemperature = pn.widgets.Checkbox(name='Temperature')
    checkboxHumidity = pn.widgets.Checkbox(name='Humidity')
    checkboxCarbon = pn.widgets.Checkbox(name='Carbon Monoxide')

    chart_container = pn.Column(
        pn.pane.Markdown("### Waiting for data...", height=300), 
        sizing_mode='stretch_width',
        min_height=300 
    )

    location_selector = pn.widgets.RadioBoxGroup(
        name='Locations',
        options=['Terezian', 'Tiglari', 'Centru', 'Caposu', 'Vasile Aron', 'Gusterita', 'Selimbar'],
        value='Centru',
        inline=True     
    )

    parameter_selector = pn.widgets.RadioBoxGroup(
        name='Parameters',
        options=['Temperature', 'Humidity', 'Carbon Monoxide'],
        value='Temperature',
        inline=True     
    )

    today = dt.date.today()
    date_range_picker = pn.widgets.DateRangePicker(
        name='Date Range Picker', value=(today, today)
    )
    
    datetime_picker = pn.widgets.DatetimePicker(
        name='Selectează Ora din Istoric', 
        value=dt.datetime.now(),
    )
    
    counter = pn.widgets.IntInput(value=0, visible=False)
    chart_trigger = pn.widgets.IntInput(value=0, visible=False)

    def toggle_specific_sensors(event):
        if event.new:
            checkboxTemperature.value = False
            checkboxHumidity.value = False
            checkboxCarbon.value = False

    def toggle_all_checkbox(event):
        if event.new: 
            checkbox.value = False

    checkbox.param.watch(toggle_specific_sensors, 'value')
    
    checkboxTemperature.param.watch(toggle_all_checkbox, 'value')
    checkboxHumidity.param.watch(toggle_all_checkbox, 'value')
    checkboxCarbon.param.watch(toggle_all_checkbox, 'value')


    

    @pn.depends(date_range_picker.param.value, datetime_picker.param.value, location_selector.param.value, watch=True)
    def fetch_data_from_api(date_range=None, datetime_value=None, location_selector_value="Centru"):
        global df_api_data

        if datetime_picker.disabled:
            datetime_picker.disabled = False

        print(f"location_selector_value: {location_selector_value}")

        deviceId = getDeviceIdsFromSelections(location_selector_value)

        print(f"datetime_value selected: {datetime_value}")
        print(f"date_range selected: {date_range}")
            
        start_sec, stop_sec = get_api_intervals(date_range)

        start = 140341
        stop = 53941

        print(f"Fetching historical data from API for range: start={start}, stop={stop}")

        try:
            api_headers = {
                "X-User-id": USER_ID,
                "X-User-hash": USER_HASH               
            }

            api_url = f"{API_URL}/{deviceId}/all/{start}/{stop}"
            # https://data.uradmonitor.com/api/v1/devices/1600013B/all/920914/834514
            response = requests.get(api_url, headers=api_headers, timeout=3)

            print("API Request URL:", api_url)
            print(f"API Response Status: {response.status_code}")

            try:

                api_headers = {"X-User-id": USER_ID, "X-User-hash": USER_HASH}
                response = requests.get(api_url, headers=api_headers, timeout=5)

                if response.status_code == 200:
                    api_data = response.json()
                    
                    if isinstance(api_data, list) and len(api_data) > 0:

                        print("--- FIRST API OBJECT ---")
                    
                        print(json.dumps(api_data[0], indent=4)) 
                        print("------------------------")
                      
                        new_df = pd.DataFrame(api_data)
                        
                       
                        if 'time' in new_df.columns:
                            new_df['timestamp'] = pd.to_datetime(new_df['time'], unit='s')
                            
                        new_df = new_df.sort_values('timestamp')
                        
                        df_api_data = new_df
                        
                
                        chart_trigger.value += 1
               

                    if len(api_data) > 0:
                        last_item = api_data[-1]
                        
                        s_id = "1600013B" 
                        if s_id in current_state:
                            current_state[s_id]["temp"] = float(last_item.get("temperature", 0))
                            current_state[s_id]["humidity"] = float(last_item.get("humidity", 0))
                            current_state[s_id]["carbon"] = float(last_item.get("pm25", 0)) 

                else:
                    print(f"API Error: {response.status_code}")

            except Exception as e:
                print(f"Error fetching data: {e}")

        except Exception as e:
            print(f"Error fetching data: {e}")

    @pn.depends(checkbox.param.value, checkboxTemperature.param.value, checkboxHumidity.param.value, checkboxCarbon.param.value, watch=True)
    def fetch_data_for_map(all=None, temperature=None, humidity=None, carbon=None):
        global df_api_data

        try:
            api_headers = {
                "X-User-id": USER_ID,
                "X-User-hash": USER_HASH               
            }

            
            # https://data.uradmonitor.com/api/v1/devices/1600013B/all/920914/834514
            response = requests.get(API_URL, headers=api_headers, timeout=3)

            print("API Request URL:", API_URL)
            print(f"API Response Status: {response.status_code}")

            try:
                if response.status_code == 200:
                    api_data = response.json() 
                    
                    for item in api_data:
                        api_id = item.get("id")         
                        temp_value = item.get("last_temperature")
                        humidity_value = item.get("last_humidity")
                        carbon_value = item.get("last_pm25")
                        # api_id = item.get("1600013B")
                        # temp_value = item.get("temperature")
                        # humidity_value = item.get("humidity")
                        # carbon_value = item.get("pm25")

                        # print(f"Processing data for sensor {api_id}: Temp={temp_value}, Humidity={humidity_value}, Carbon={carbon_value}")

                        if api_id in current_state:
                            
                    
                            if temp_value is not None:
                                current_state[api_id]["temp"] = float(temp_value)
                                current_state[api_id]["humidity"] = float(humidity_value)
                                current_state[api_id]["carbon"] = float(carbon_value)

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
            


        except Exception as e:
            print(f"Error fetching data: {e}")
    pn.state.add_periodic_callback(fetch_data_for_map, period=300000)
    pn.state.onload(fetch_data_for_map)
    pn.state.onload(fetch_data_from_api)

    def generate_popup_content(all_checked, temp_checked, humidity_checked, carbon_checked, senzor_meta, status, temp, humidity, carbon, timestamp_str):
        content = f"<div style='min-width: 140px'><b>{senzor_meta['name']}</b><br><small>Data: {timestamp_str}</small><hr style='margin:5px 0'>Status: <b>{status}</b><br>"
        
        if all_checked:
            content += f"Temp: <b>{temp:.1f} °C</b><br>Humidity: <b>{humidity:.1f} %</b><br>Carbon Monoxide: <b>{carbon:.1f} ppm</b><br>"
        else:
            if temp_checked:
                content += f"Temp: <b>{temp:.1f} °C</b><br>"
            if humidity_checked:
                content += f"Humidity: <b>{humidity:.1f} %</b><br>"
            if carbon_checked:
                content += f"Carbon Monoxide: <b>{carbon:.1f} ppm</b><br>"
        
        content += "</div>"
        return content

    @pn.depends(counter.param.value, datetime_picker.param.value, checkbox.param.value, checkboxTemperature.param.value, checkboxHumidity.param.value, checkboxCarbon.param.value)
    def get_map(tick, selected_time, all_checked, temp_checked, humidity_checked, carbon_checked):
        
        m = folium.Map(location=[45.7983, 24.1256], zoom_start=13)
        
        for senzor_meta in metadata_senzori:
            s_id = senzor_meta['id']
            
            temp = 0.0
            humidity = 0.0
            carbon = 0.0
            status = "N/A"
            timestamp_str = "Acum"

        
            data = current_state[s_id]
            temp = data['temp']
            humidity = data['humidity']
            carbon = data['carbon']
            status = data['status']
        
            color = 'green'
            if status == 'Inactiv' or status == 'Fără Date': color = 'gray'
            elif status == 'Alertă': color = 'red'

            popup_content = generate_popup_content(all_checked, temp_checked, humidity_checked, carbon_checked, senzor_meta, status, temp, humidity, carbon, timestamp_str)
            folium.Marker(
                location=[senzor_meta['lat'], senzor_meta['lon']],
                popup=popup_content,
                tooltip=popup_content,
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)

        return pn.pane.plot.Folium(m, height=400)

    @pn.depends(chart_trigger.param.value, parameter_selector.param.value,  watch=True)
    def update_chart_view(c, parameter_selector):
        new_content = get_temperature_plot(parameter_selector)
        
        chart_container.objects = [new_content]


    control_row = pn.Row(
        checkbox,
        checkboxTemperature,
        checkboxHumidity,
        checkboxCarbon,
        date_range_picker,
        datetime_picker
    )
    
    layout = pn.Column(
        control_row,
        counter,
        chart_trigger,
        get_map,
        pn.layout.Divider(),
        pn.pane.Markdown("## Historical Data Analysis"),
        location_selector,
        parameter_selector,
        chart_container,
        sizing_mode='stretch_width'
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