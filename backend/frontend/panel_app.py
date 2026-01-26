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
from .util_functions import getParameter, get_api_intervals, getDeviceIdsFromSelections, generate_popup_content
from .css import date_picker_style, my_custom_style, checkbox_style_square

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


df_api_data = pd.DataFrame()

def get_temperature_plot(parameter_selector):
    if df_api_data.empty:
        return pn.pane.Markdown("### Waiting for data...")
    
    parameter_data = getParameter(parameter_selector)
    param_name = parameter_data["parameter"]
    
    data_min = df_api_data[param_name].min()
    data_max = df_api_data[param_name].max()
    
    padding = (data_max - data_min) * 0.1 if data_max != data_min else 1.0
    
    if pd.isna(data_min): data_min = 0
    if pd.isna(data_max): data_max = 10

    domain_start = data_min - padding
    domain_end = data_max + padding

    background_zones = []

    if 'temperature' in param_name.lower():
        background_zones = [
            {'y_start': -0, 'y_end': -30, 'color': "#3D92AF", 'label': 'Cold (<10°C)'},    
            {'y_start': -0, 'y_end': 10, 'color': '#ADD8E6', 'label': 'Cold (<10°C)'},    
            {'y_start': 10, 'y_end': 20, 'color': "#8BF89A", 'label': 'Comfortable'},   
            {'y_start': 20, 'y_end': 30, 'color': '#FFCCCC', 'label': 'Warm'},     
            {'y_start': 30, 'y_end': 60, 'color': "#F87070", 'label': 'Hot (>30°C)'}     
        ]

    elif 'humidity' in param_name.lower():
        background_zones = [
          
            {'y_start': 0, 'y_end': 30, 'color': '#FFFACD', 'label': 'Dry (<30%)'},       
         
            {'y_start': 30, 'y_end': 70, 'color': '#D0F0C0', 'label': 'Comfortable'},      
            
            {'y_start': 70, 'y_end': 100, 'color': '#E0FFFF', 'label': 'Humid (>70%)'}    
        ]

    elif 'pm25' in param_name.lower() or 'carbon' in param_name.lower():
        background_zones = [
          
            {'y_start': 0, 'y_end': 50, 'color': '#D0F0C0', 'label': 'Good'},             
            
            {'y_start': 51, 'y_end': 100, 'color': '#FFFACD', 'label': 'Moderate'},        
            
            {'y_start': 101, 'y_end': 150, 'color': '#FFCC99', 'label': 'Unhealthy'},       
            
            {'y_start': 151, 'y_end': 200, 'color': '#FFCCCC', 'label': 'Very Unhealthy'}       
        ]

    df_bg = pd.DataFrame(background_zones)

    bg_chart = alt.Chart(df_bg).mark_rect(opacity=0.4).encode(
        y='y_start:Q',
        y2='y_end:Q',
        color=alt.Color('color:N', scale=None),
        tooltip='label'
    )

    line_chart = alt.Chart(df_api_data).mark_line(point=True).encode(
        x=alt.X('timestamp:T', title='Time', axis=alt.Axis(format='%H:%M')),
        y=alt.Y(
            f'{param_name}:Q', 
            title=f'{parameter_data["subtitle"]}',
            scale=alt.Scale(domain=[domain_start, domain_end]) 
        ),
        color=alt.Color('Location:N', legend=alt.Legend(title="Locations")), 
        tooltip=[
            alt.Tooltip('timestamp:T', format='%Y-%m-%d %H:%M'), 
            'Location',
            'temperature', 
            'humidity', 
            'pm25'
        ]
    )

    # --- 5. LAYER AND COMBINE ---
    final_chart = alt.layer(bg_chart, line_chart).properties(
        title=parameter_data["title"],
        height=500,
        width='container'
    ).interactive()

    return pn.pane.Vega(final_chart, sizing_mode='stretch_width')


def render_dashboard_page():
    pn.extension('vega')
    
    # --- WIDGETS ---
    
    checkbox = pn.widgets.Checkbox(
        name='All', 
        value=True, 
        css_classes=['styled-checkbox'], 
        stylesheets=[checkbox_style_square]
    )
    
    checkboxTemperature = pn.widgets.Checkbox(
        name='Temperature', 
        css_classes=['styled-checkbox'], 
        stylesheets=[checkbox_style_square]
    )
    
    checkboxHumidity = pn.widgets.Checkbox(
        name='Humidity', 
        css_classes=['styled-checkbox'], 
        stylesheets=[checkbox_style_square]
    )
    
    checkboxCarbon = pn.widgets.Checkbox(
        name='Carbon Monoxide', 
        css_classes=['styled-checkbox'], 
        stylesheets=[checkbox_style_square]
    )

    # Le punem într-un rând cu spațiere (gap) ca să respire designul
    control_row = pn.Row(
        checkbox,
        checkboxTemperature,
        checkboxHumidity,
        checkboxCarbon,
        sizing_mode='stretch_width',
        styles={'gap': '20px', 'align-items': 'center'} # Spațiu între ele
    )

    chart_container = pn.Column(
        pn.pane.Markdown("### Waiting for data...", height=300), 
        sizing_mode='stretch_width',
        min_height=300 
    )

    # location_selector = pn.widgets.RadioBoxGroup(
    #     name='Locations',
    #     options=['Terezian', 'Tiglari', 'Centru', 'Caposu', 'Vasile Aron', 'Gusterita', 'Selimbar'],
    #     value='Centru',
    #     inline=True,
    #    css_classes=['location-selector'],
    #     # AICI ESTE SECRETUL PENTRU PANEL 1.0+:
    #     stylesheets=[my_custom_style]  
    # )
    # Change from RadioBoxGroup to CheckBoxGroup to allow multiple selections
    location_selector = pn.widgets.CheckBoxGroup(
        name='Locations',
        options=['Terezian', 'Tiglari', 'Centru', 'Caposu', 'Vasile Aron', 'Gusterita', 'Selimbar'],
        value=['Centru'], # Default is now a list
        inline=True,
        css_classes=['location-selector'],
        stylesheets=[my_custom_style]  
    )

    parameter_selector = pn.widgets.RadioBoxGroup(
        name='Parameters',
        options=['Temperature', 'Humidity', 'Carbon Monoxide'],
        value='Temperature',
        inline=True,
        css_classes=['location-selector'],
        # AICI ESTE SECRETUL PENTRU PANEL 1.0+:
        stylesheets=[my_custom_style]       
    )

    today = dt.date.today()
    date_range_picker = pn.widgets.DateRangePicker(
        name='Date Range Picker', value=(today, today),
        css_classes=['my-date-picker'], # Clasa de identificare
        stylesheets=[date_picker_style], # Injectăm CSS-ul direct
        sizing_mode='stretch_width'
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

    

    # @pn.depends(date_range_picker.param.value, datetime_picker.param.value, location_selector.param.value, watch=True)
    # def fetch_data_from_api(date_range=None, datetime_value=None, location_selector_value="Centru"):
    #     global df_api_data

    #     if datetime_picker.disabled:
    #         datetime_picker.disabled = False

    #     print(f"location_selector_value: {location_selector_value}")

    #     deviceId = getDeviceIdsFromSelections(location_selector_value)

    #     print(f"datetime_value selected: {datetime_value}")
    #     print(f"date_range selected: {date_range}")
            
    #     start_sec, stop_sec = get_api_intervals(date_range)

    #     start = 140341
    #     stop = 53941

    #     # print(f"Fetching historical data from API for range: start={start}, stop={stop}")
    #     print(f"Fetching historical data from API for range: start2={start_sec}, stop2={stop_sec}")


    #     try:
    #         api_headers = {
    #             "X-User-id": USER_ID,
    #             "X-User-hash": USER_HASH               
    #         }

    #         api_url = f"{API_URL}/{deviceId}/all/{start_sec}/{stop_sec}"
    #         # https://data.uradmonitor.com/api/v1/devices/1600013B/all/920914/834514
    #         response = requests.get(api_url, headers=api_headers, timeout=3)

    #         print("API Request URL:", api_url)
    #         print(f"API Response Status: {response.status_code}")

    #         try:

    #             api_headers = {"X-User-id": USER_ID, "X-User-hash": USER_HASH}
    #             response = requests.get(api_url, headers=api_headers, timeout=5)

    #             if response.status_code == 200:
    #                 api_data = response.json()
                    
    #                 if isinstance(api_data, list) and len(api_data) > 0:

    #                     new_df = pd.DataFrame(api_data)
                        
    #                     if 'time' in new_df.columns:
    #                         new_df['timestamp'] = pd.to_datetime(new_df['time'], unit='s')
                            
    #                     new_df = new_df.sort_values('timestamp')
                        
    #                     df_api_data = new_df
                        
                
    #                     chart_trigger.value += 1
               

    #                 if len(api_data) > 0:
    #                     last_item = api_data[-1]
                        
    #                     s_id = "1600013B" 
    #                     if s_id in current_state:
    #                         current_state[s_id]["temp"] = float(last_item.get("temperature", 0))
    #                         current_state[s_id]["humidity"] = float(last_item.get("humidity", 0))
    #                         current_state[s_id]["carbon"] = float(last_item.get("pm25", 0)) 

    #             else:
    #                 print(f"API Error: {response.status_code}")

    #         except Exception as e:
    #             print(f"Error fetching data: {e}")

    #     except Exception as e:
    #         print(f"Error fetching data: {e}")

    @pn.depends(date_range_picker.param.value, datetime_picker.param.value, location_selector.param.value, watch=True)
    def fetch_data_from_api(date_range=None, datetime_value=None, location_selector_value="Centru"):
        global df_api_data

        # Ensure location_selector_value is a list (handling initial load)
        if not isinstance(location_selector_value, list):
            location_selector_value = [location_selector_value]

        if not location_selector_value:
            print("No location selected")
            return

        if datetime_picker.disabled:
            datetime_picker.disabled = False

        start_sec, stop_sec = get_api_intervals(date_range)
        
        # Store all dataframes here before concatenating
        all_data_frames = []

        # --- LOOP THROUGH ALL SELECTED LOCATIONS ---
        for loc_name in location_selector_value:
            try:
                # We assume getDeviceIdsFromSelections returns the ID for a specific name
                # If your function expects a string, we pass loc_name directly
                deviceId = getDeviceIdsFromSelections(loc_name)
                
                if not deviceId:
                    print(f"No ID found for {loc_name}")
                    continue

                api_headers = {
                    "X-User-id": USER_ID,
                    "X-User-hash": USER_HASH               
                }

                api_url = f"{API_URL}/{deviceId}/all/{start_sec}/{stop_sec}"
                
                # API Request
                response = requests.get(api_url, headers=api_headers, timeout=5)

                if response.status_code == 200:
                    api_data = response.json()
                    
                    if isinstance(api_data, list) and len(api_data) > 0:
                        new_df = pd.DataFrame(api_data)
                        
                        if 'time' in new_df.columns:
                            new_df['timestamp'] = pd.to_datetime(new_df['time'], unit='s')
                        
                        # IMPORTANT: Add the location name to this specific data chunk
                        new_df['Location'] = loc_name 
                        
                        # Append to our list
                        all_data_frames.append(new_df)
                        
                        # Update current state for the map/markers (optional, uses the last point)
                        if len(api_data) > 0:
                            last_item = api_data[-1]
                            # Note: You might need logic here to map deviceId back to metadata IDs if they differ
                            if deviceId in current_state:
                                current_state[deviceId]["temp"] = float(last_item.get("temperature", 0))
                                current_state[deviceId]["humidity"] = float(last_item.get("humidity", 0))
                                current_state[deviceId]["carbon"] = float(last_item.get("pm25", 0))
                else:
                    print(f"API Error for {loc_name}: {response.status_code}")

            except Exception as e:
                print(f"Error processing {loc_name}: {e}")

        # --- COMBINE ALL DATA ---
        if all_data_frames:
            combined_df = pd.concat(all_data_frames)
            combined_df = combined_df.sort_values('timestamp')
            df_api_data = combined_df
            
            # Trigger the chart update
            chart_trigger.value += 1
        else:
            print("No data fetched for any location.")
            df_api_data = pd.DataFrame()

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


    @pn.depends(counter.param.value, datetime_picker.param.value, checkbox.param.value, checkboxTemperature.param.value, checkboxHumidity.param.value, checkboxCarbon.param.value)
    def get_map(tick, selected_time, all_checked, temp_checked, humidity_checked, carbon_checked):
        
        m = folium.Map(location=[45.7983, 24.1256], zoom_start=13)

        css_fix = """
        <style>
            @media (hover: none), (max-width: 768px) {
                .leaflet-tooltip {
                    display: none !important;
                }
            }
        </style>
        """

        m.get_root().header.add_child(folium.Element(css_fix))
        
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

    
    layout = pn.Column(
        control_row,
        counter,
        chart_trigger,
        get_map,
        pn.layout.Divider(),
        pn.pane.Markdown("## Historical Data Analysis"),
        location_selector,
        parameter_selector,
        date_range_picker,
        # datetime_picker,
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


# def run_panel_server():
#     allowed_origin = os.getenv("RENDER_EXTERNAL_HOSTNAME", "127.0.0.1")
    
#     origins = [
#         allowed_origin,          
#         "127.0.0.1:5000",       
#         "127.0.0.1:5001",       
#         "localhost:5000",
#         "localhost:5001"
#     ]

#     pn.serve(
#         {'/dashboard': render_dashboard_page, '/admin': render_admin_page}, 
#         port=5006, 
#         allow_websocket_origin=origins, 
#         address="0.0.0.0", 
#         show=False,
#         loop=None
#     )

# t = threading.Thread(target=run_panel_server, daemon=True)
# t.start()