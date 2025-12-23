import panel as pn
import folium
import altair as alt
import pandas as pd
import datetime as dt
import random
import threading
import numpy as np

senzori = [
    {
        "name": "Senzor Piața Mare",
        "lat": 45.7973,     
        "lon": 24.1521,
        "status": "Activ",
        "value": 22.0       
    },
    {
        "name": "Senzor Zona Industrială Vest",
        "lat": 45.7950,
        "lon": 24.1100,
        "status": "Activ",
        "value": 24.0
    },
    {
        "name": "Senzor Aeroport",
        "lat": 45.7870,
        "lon": 24.0910,
        "status": "Inactiv",
        "value": 0.0     
    },
    {
        "name": "Senzor Shopping City",
        "lat": 45.7680,
        "lon": 24.1500,
        "status": "Alertă",
        "value": 35.0
    }

    
]

metadata_senzori = [
    {"id": "s1", "name": "Senzor Piața Mare", "lat": 45.7973, "lon": 24.1521},
    {"id": "s2", "name": "Senzor Zona Ind. Vest", "lat": 45.7950, "lon": 24.1100},
    {"id": "s3", "name": "Senzor Aeroport", "lat": 45.7870, "lon": 24.0910},
    {"id": "s4", "name": "Senzor Shopping City", "lat": 45.7680, "lon": 24.1500},
]

current_state = {s['id']: {"value": 20.0, "status": "Activ"} for s in metadata_senzori}


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
    def update_inputs(is_live):
        datetime_picker.disabled = is_live
        if is_live:
            mode_label.value = '<b>Live Mode</b> (Date în timp real)'
        else:
            mode_label.value = '<b>History Mode</b> (Date din arhivă)'

    def simulate_live_data():
        if mode_switch.value:
            for s_id in current_state:
            
                change = random.choice([-0.2, 0, 0.2])
                current_state[s_id]["value"] += change
                
            
                if current_state[s_id]["value"] > 30:
                    current_state[s_id]["status"] = "Alertă"
                else:
                    current_state[s_id]["status"] = "Activ"
            
            counter.value += 1

    pn.state.add_periodic_callback(simulate_live_data, period=1000)

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