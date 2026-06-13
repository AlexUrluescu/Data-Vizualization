import panel as pn
import folium
import altair as alt
import pandas as pd
import datetime as dt
import numpy as np
import requests
import os
from dotenv import load_dotenv
from db import init_db, list_sensors
from fetch import fetch_location_data
from datetime import datetime, timezone
import altair as alt
from .util_functions import getParameter, get_api_intervals, generate_popup_content
from insights import generate_period_insights
from forecast import train_and_forecast
from chat import ChatAgent
from .navbar import render_navbar
from .css import (
    date_picker_style, my_custom_style, checkbox_style_square,
    card_style, chart_container_style, map_container_style,
    FONT_IMPORT, global_style, section_label, divider_style,
    forecast_card_style, chat_card_style, chat_bubble_css,
)

alt.data_transformers.disable_max_rows()
load_dotenv()
init_db()

API_URL = os.getenv("API_URL")
USER_ID = os.getenv("USER_ID")
USER_HASH = os.getenv("USER_HASH")

# metadata_senzori = [
#     {"id": "1600013B", "name": "Centru", "lat": 45.7982683, "lon": 24.1488102},
#     {"id": "1600019F", "name": "Terezian", "lat": 45.807144, "lon": 24.145801},
#     {"id": "16000284", "name": "Vasile Aron", "lat": 45.786566, "lon": 24.16383},
#     {"id": "16000224", "name": "Tiglari", "lat": 45.80865637, "lon": 24.14074895},
#     {"id": "16000341", "name": "Vestem", "lat": 45.7163527, "lon": 24.23857099},
#     {"id": "16000342", "name": "Selimbar", "lat": 45.76698129, "lon": 24.19551811},
#     {"id": "16000343", "name": "Gusterita", "lat": 45.810222, "lon": 24.179481},
#     {"id": "16000344", "name": "Mohu", "lat": 45.7429537, "lon": 24.2231919},
#     {"id": "8200029B", "name": "Caposu", "lat": 45.793112, "lon": 24.152697},
# ]

metadata_senzori = [
    {"id": s["id"], "name": s["name"], "lat": s["lat"], "lon": s["lon"]}
    for s in list_sensors()
    if s["is_active"]  # only active sensors
]

current_state = {s['id']: {"temp": 0.0, "status": "Activ", "humidity": 0.0, "carbon": 0.0} for s in metadata_senzori}

df_api_data = pd.DataFrame()


# ── Altair chart ──────────────────────────────────────────────
def get_temperature_plot(parameter_selector):
    if df_api_data.empty:
        return pn.pane.Markdown(
            "### ⏳ Waiting for data...",
            styles={
                "color": "#7B82B4",
                "text-align": "center",
                "padding": "60px 0",
                "font-family": "'DM Sans', sans-serif",
            }
        )

    parameter_data = getParameter(parameter_selector)
    param_name = parameter_data["parameter"]

    data_min = df_api_data[param_name].min()
    data_max = df_api_data[param_name].max()
    padding = (data_max - data_min) * 0.1 if data_max != data_min else 1.0
    if pd.isna(data_min): data_min = 0
    if pd.isna(data_max): data_max = 10

    domain_start = data_min - padding
    domain_end   = data_max + padding

    background_zones = []

    if 'temperature' in param_name.lower():
        background_zones = [
            {'y_start': -30, 'y_end': 0,  'color': "#B8E4F5", 'label': 'Freezing (<0°C)'},
            {'y_start':   0, 'y_end': 10, 'color': "#D6EEF8", 'label': 'Cold (<10°C)'},
            {'y_start':  10, 'y_end': 20, 'color': "#C8F5D0", 'label': 'Comfortable'},
            {'y_start':  20, 'y_end': 30, 'color': "#FFE4C4", 'label': 'Warm'},
            {'y_start':  30, 'y_end': 60, 'color': "#FFB8B8", 'label': 'Hot (>30°C)'},
        ]
    elif 'humidity' in param_name.lower():
        background_zones = [
            {'y_start':  0, 'y_end': 30,  'color': '#FFF5CC', 'label': 'Dry (<30%)'},
            {'y_start': 30, 'y_end': 70,  'color': '#D0F0C0', 'label': 'Comfortable'},
            {'y_start': 70, 'y_end': 100, 'color': '#C8E8FF', 'label': 'Humid (>70%)'},
        ]
    elif 'pm25' in param_name.lower() or 'carbon' in param_name.lower():
        background_zones = [
            {'y_start':   0, 'y_end':  50,  'color': '#C8F5D0', 'label': 'Good'},
            {'y_start':  51, 'y_end': 100,  'color': '#FFF5CC', 'label': 'Moderate'},
            {'y_start': 101, 'y_end': 150,  'color': '#FFE0B0', 'label': 'Unhealthy'},
            {'y_start': 151, 'y_end': 200,  'color': '#FFB8B8', 'label': 'Very Unhealthy'},
        ]

    df_bg = pd.DataFrame(background_zones)

    bg_chart = alt.Chart(df_bg).mark_rect(opacity=0.35).encode(
        y='y_start:Q',
        y2='y_end:Q',
        color=alt.Color('color:N', scale=None),
        tooltip='label'
    )

    # Pastel color palette for multi-location lines
    pastel_palette = [
        "#7C9EFF", "#F9A8D4", "#6EE7B7", "#FCD34D",
        "#C4B5FD", "#FCA5A5", "#67E8F9", "#A3E635",
    ]

    line_chart = alt.Chart(df_api_data).mark_line(
        point=alt.OverlayMarkDef(filled=True, size=60),
        strokeWidth=2.5
    ).encode(
        x=alt.X(
            'timestamp:T',
            title='Time',
            axis=alt.Axis(
                format='%H:%M',
                labelFont='DM Sans',
                titleFont='DM Sans',
                labelColor='#7B82B4',
                titleColor='#5A5F94',
                gridColor='#F0F2FA',
                domainColor='#E0E4F5',
            )
        ),
        y=alt.Y(
            f'{param_name}:Q',
            title=parameter_data["subtitle"],
            scale=alt.Scale(domain=[domain_start, domain_end]),
            axis=alt.Axis(
                labelFont='DM Sans',
                titleFont='DM Sans',
                labelColor='#7B82B4',
                titleColor='#5A5F94',
                gridColor='#F0F2FA',
                domainColor='#E0E4F5',
            )
        ),
        color=alt.Color(
            'Location:N',
            scale=alt.Scale(range=pastel_palette),
            legend=alt.Legend(
                title="Locations",
                titleFont='DM Sans',
                labelFont='DM Sans',
                titleColor='#5A5F94',
                labelColor='#2D2F3E',
            )
        ),
        tooltip=[
            alt.Tooltip('timestamp:T', format='%Y-%m-%d %H:%M'),
            'Location',
            'temperature',
            'humidity',
            'pm25',
        ]
    )

    final_chart = (
        alt.layer(bg_chart, line_chart)
        .properties(
            title=alt.TitleParams(
                parameter_data["title"],
                font='DM Sans',
                fontSize=15,
                fontWeight=600,
                color='#2D2F3E',
                anchor='start',
                offset=8,
            ),
            height=460,
            width='container',
            background='#FFFFFF',
        )
        .configure_view(
            strokeWidth=0,
        )
        .interactive()
    )

    return pn.pane.Vega(final_chart, sizing_mode='stretch_width')


def create_social_media_card(df, parameter_name="pm25"):
    insights = generate_period_insights(df, parameter_name)
    
    if "error" in insights:
        return pn.pane.Markdown(f"### ⚠️ {insights['error']}", styles={"color": "red"})

    if parameter_name == 'temperature':
        param_label = "Temperatură"
        unit = "°C"
        t_day = "Cea mai călduroasă zi"
        t_hour = "Ora cea mai caldă (Media)"
        t_clean = "Zona cea mai răcoroasă"
        t_worst = "Zona cea mai caldă"
    elif parameter_name == 'humidity':
        param_label = "Umiditate"
        unit = "%"
        t_day = "Cea mai umedă zi"
        t_hour = "Ora cea mai umedă (Media)"
        t_clean = "Zona cea mai uscată"
        t_worst = "Zona cea mai umedă"
    else:
        param_label = "Calitatea Aerului (CO / PM2.5)"
        unit = "µg/m³" # sau ppm, în funcție de ce citește senzorul exact
        t_day = "Cea mai poluată zi"
        t_hour = "Ora de evitat (Poluare maximă)"
        t_clean = "Zona cea mai curată"
        t_worst = "Zona cea mai poluată"

    # HTML-ul folosește acum variabilele definite mai sus
    html_content = f"""
    <div style="
        width: 100%; margin: 0 auto; 
        background: linear-gradient(135deg, #FFFFFF 0%, #F7F8FC 100%);
        border-radius: 20px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        font-family: 'DM Sans', sans-serif; color: #2D2F3E; border: 1px solid #EEF0FA;">
        
        <h2 style="color: #4B51A0; margin-top: 0; font-size: 24px; text-align: center;">
            📊 Retrospectiva Sibiului
        </h2>
        <p style="text-align: center; color: #7B82B4; font-size: 14px; margin-bottom: 30px; text-transform: uppercase; letter-spacing: 1px;">
            {param_label}
        </p>

        <div style="background: #FFF; border-radius: 12px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #FFB8B8; box-shadow: 0 2px 10px rgba(0,0,0,0.02);">
            <div style="font-size: 12px; color: #7B82B4; text-transform: uppercase;">{t_day}</div>
            <div style="font-size: 18px; font-weight: bold; color: #2D2F3E;">{insights['worst_day_date']} <span style="color: #FF5733; font-size: 16px;">({insights['worst_day_val']} {unit})</span></div>
        </div>

        <div style="background: #FFF; border-radius: 12px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #FCD34D; box-shadow: 0 2px 10px rgba(0,0,0,0.02);">
            <div style="font-size: 12px; color: #7B82B4; text-transform: uppercase;">{t_hour}</div>
            <div style="font-size: 18px; font-weight: bold; color: #2D2F3E;">🕒 {insights['worst_hour_interval']}</div>
        </div>

        <div style="display: flex; gap: 15px; margin-bottom: 15px;">
            <div style="flex: 1; background: #FFF; border-radius: 12px; padding: 15px; border-left: 5px solid #6EE7B7; box-shadow: 0 2px 10px rgba(0,0,0,0.02);">
                <div style="font-size: 12px; color: #7B82B4; text-transform: uppercase;">{t_clean}</div>
                <div style="font-size: 16px; font-weight: bold;">{insights['cleanest_loc']}</div>
            </div>
            <div style="flex: 1; background: #FFF; border-radius: 12px; padding: 15px; border-left: 5px solid #FCA5A5; box-shadow: 0 2px 10px rgba(0,0,0,0.02);">
                <div style="font-size: 12px; color: #7B82B4; text-transform: uppercase;">{t_worst}</div>
                <div style="font-size: 16px; font-weight: bold;">{insights['worst_loc']}</div>
            </div>
        </div>

        <div style="background: #EEF0FF; border-radius: 12px; padding: 20px; text-align: center; color: #4B51A0;">
            <i>{insights['weekend_comparison'].replace('**', '<b>').replace('**', '</b>')}</i>
        </div>
        
        <div style="text-align: center; margin-top: 25px; font-size: 11px; color: #A5B4FC;">
            Generat automat prin Urban Bike Data
        </div>
    </div>
    """
    return pn.pane.HTML(html_content, sizing_mode='stretch_width')


# ── Dashboard page ─────────────────────────────────────────────
def render_dashboard_page():
    pn.extension('vega')

    metadata_senzori = [
        {"id": s["id"], "name": s["name"], "lat": s["lat"], "lon": s["lon"]}
        for s in list_sensors()
        if s["is_active"]
    ]

    name_to_id = {s["name"]: s["id"] for s in metadata_senzori}

    current_state = {
        s['id']: {"temp": 0.0, "status": "Activ", "humidity": 0.0, "carbon": 0.0}
        for s in metadata_senzori
    }


    pn.config.raw_css.append(FONT_IMPORT + global_style + divider_style)

    # ── Widgets ──────────────────────────────────────────────
    checkbox = pn.widgets.Checkbox(
        name='All',
        value=True,
        css_classes=['styled-checkbox'],
        stylesheets=[checkbox_style_square],
    )
    checkboxTemperature = pn.widgets.Checkbox(
        name='🌡 Temperature',
        css_classes=['styled-checkbox'],
        stylesheets=[checkbox_style_square],
    )
    checkboxHumidity = pn.widgets.Checkbox(
        name='💧 Humidity',
        css_classes=['styled-checkbox'],
        stylesheets=[checkbox_style_square],
    )
    checkboxCarbon = pn.widgets.Checkbox(
        name='🌫 CO / PM2.5',
        css_classes=['styled-checkbox'],
        stylesheets=[checkbox_style_square],
    )

    # Sensor filter card
    filter_card = pn.Column(
        pn.Row(
            checkbox, checkboxTemperature, checkboxHumidity, checkboxCarbon,
            sizing_mode='stretch_width',
            styles={'gap': '10px', 'flex-wrap': 'wrap', 'align-items': 'center'},
        ),
        styles=card_style,
        sizing_mode='stretch_width',
    )

    # Chart container
    chart_container = pn.Column(
        pn.pane.Markdown(
            "### ⏳ Waiting for data...",
            styles={"color": "#7B82B4", "padding": "60px 0", "text-align": "center"},
        ),
        sizing_mode='stretch_width',
        min_height=300,
        styles=chart_container_style,
    )

    location_selector = pn.widgets.CheckBoxGroup(
        name='Locations',
        options=[s["name"] for s in metadata_senzori], 
        value=[metadata_senzori[0]["name"]] if metadata_senzori else [],
        inline=True,
        css_classes=['location-selector'],
        stylesheets=[my_custom_style],
    )

    parameter_selector = pn.widgets.RadioBoxGroup(
        name='Parameters',
        options=['Temperature', 'Humidity', 'Carbon Monoxide'],
        value='Temperature',
        inline=True,
        css_classes=['location-selector'],
        stylesheets=[my_custom_style],
    )

    today = dt.date.today()
    date_range_picker = pn.widgets.DateRangePicker(
        name='Date Range',
        value=(today, today),
        css_classes=['my-date-picker'],
        stylesheets=[date_picker_style],
        sizing_mode='stretch_width',
    )

    datetime_picker = pn.widgets.DatetimePicker(
        name='Selectează Ora din Istoric',
        value=dt.datetime.now(),
    )

    counter       = pn.widgets.IntInput(value=0, visible=False)
    chart_trigger = pn.widgets.IntInput(value=0, visible=False)

    # ── Checkbox mutual-exclusion logic ──────────────────────
    def toggle_specific_sensors(event):
        if event.new:
            checkboxTemperature.value = False
            checkboxHumidity.value    = False
            checkboxCarbon.value      = False

    def toggle_all_checkbox(event):
        if event.new:
            checkbox.value = False

    checkbox.param.watch(toggle_specific_sensors, 'value')
    checkboxTemperature.param.watch(toggle_all_checkbox, 'value')
    checkboxHumidity.param.watch(toggle_all_checkbox, 'value')
    checkboxCarbon.param.watch(toggle_all_checkbox, 'value')

    # ── API: historical time-series ───────────────────────────
    @pn.depends(date_range_picker.param.value, datetime_picker.param.value, location_selector.param.value, watch=True)
    def fetch_data_from_api(date_range=None, datetime_value=None, location_selector_value="Centru"):
        global df_api_data

        chart_container.loading = True

        if not isinstance(location_selector_value, list):
            location_selector_value = [location_selector_value]
        if not location_selector_value:
            chart_container.loading = False
            return

        # ← Guard: if no date range yet, fall back to today
        if not date_range or date_range[0] is None:
            date_range = (dt.date.today(), dt.date.today())

        if datetime_picker.disabled:
            datetime_picker.disabled = False

        start_dt, end_dt = get_api_intervals(date_range)

        if start_dt is None or end_dt is None:
            chart_container.loading = False
            return


        all_data_frames = []

        for loc_name in location_selector_value:
            try:
                device_id = name_to_id.get(loc_name, "")
                if not device_id:
                    continue

                df = fetch_location_data(device_id, loc_name, start_dt, end_dt)

                if not df.empty:
                    all_data_frames.append(df)
                    last = df.iloc[-1]
                    if device_id in current_state:
                        current_state[device_id]["temp"]     = float(last.get("temperature") or 0)
                        current_state[device_id]["humidity"] = float(last.get("humidity") or 0)
                        current_state[device_id]["carbon"]   = float(last.get("pm25") or 0)

            except Exception as e:
                print(f"Error processing {loc_name}: {e}")

        if all_data_frames:
            df_api_data = pd.concat(all_data_frames).sort_values("timestamp")
            chart_trigger.value += 1
        else:
            df_api_data = pd.DataFrame()
            chart_trigger.value += 1  

        chart_container.loading = False
    # ── API: current map data ─────────────────────────────────
    @pn.depends(
        checkbox.param.value,
        checkboxTemperature.param.value,
        checkboxHumidity.param.value,
        checkboxCarbon.param.value,
        watch=True,
    )
    def fetch_data_for_map(all=None, temperature=None, humidity=None, carbon=None):
        global df_api_data
        try:
            api_headers = {"X-User-id": USER_ID, "X-User-hash": USER_HASH}
            response = requests.get(API_URL, headers=api_headers, timeout=3)
            if response.status_code == 200:
                api_data = response.json()
                for item in api_data:
                    api_id        = item.get("id")
                    temp_value    = item.get("last_temperature")
                    humidity_value = item.get("last_humidity")
                    carbon_value  = item.get("last_pm25")
                    if api_id in current_state and temp_value is not None:
                        current_state[api_id]["temp"]     = float(temp_value)
                        current_state[api_id]["humidity"] = float(humidity_value)
                        current_state[api_id]["carbon"]   = float(carbon_value)
                        if float(temp_value) == 0:
                            current_state[api_id]["status"] = "Inactiv"
                        elif float(temp_value) > 30:
                            current_state[api_id]["status"] = "Alertă"
                        else:
                            current_state[api_id]["status"] = "Activ"
                counter.value += 1
        except Exception as e:
            print(f"Error fetching map data: {e}")

    pn.state.add_periodic_callback(fetch_data_for_map, period=300000)
    pn.state.onload(fetch_data_for_map)
    pn.state.onload(lambda: fetch_data_from_api(
        date_range=date_range_picker.value,
        datetime_value=datetime_picker.value,
        location_selector_value=location_selector.value,
    ))

    # ── Map renderer ─────────────────────────────────────────
    @pn.depends(
        counter.param.value,
        datetime_picker.param.value,
        checkbox.param.value,
        checkboxTemperature.param.value,
        checkboxHumidity.param.value,
        checkboxCarbon.param.value,
    )
    def get_map(tick, selected_time, all_checked, temp_checked, humidity_checked, carbon_checked):
        m = folium.Map(
            location=[45.7983, 24.1256],
            zoom_start=13,
            tiles='CartoDB positron',  
        )

      
        m.get_root().header.add_child(folium.Element("""
        <style>
            @media (hover: none), (max-width: 768px) {
                .leaflet-tooltip { display: none !important; }
            }
        </style>
        """))

        for senzor_meta in metadata_senzori:
            s_id = senzor_meta['id']
            data  = current_state[s_id]
            temp     = data['temp']
            humidity = data['humidity']
            carbon   = data['carbon']
            status   = data['status']
            timestamp_str = "Acum"

            color = 'green'
            if status in ('Inactiv', 'Fără Date'):
                color = 'gray'
            elif status == 'Alertă':
                color = 'red'

            popup_content = generate_popup_content(
                all_checked, temp_checked, humidity_checked, carbon_checked,
                senzor_meta, status, temp, humidity, carbon, timestamp_str,
            )
            folium.Marker(
                location=[senzor_meta['lat'], senzor_meta['lon']],
                popup=popup_content,
                tooltip=popup_content,
                icon=folium.Icon(color=color, icon='info-sign'),
            ).add_to(m)

        return pn.pane.plot.Folium(m, height=400, styles=map_container_style)

    # ── Chart updater ─────────────────────────────────────────
    @pn.depends(chart_trigger.param.value, parameter_selector.param.value, watch=True)
    def update_chart_view(c, parameter_selector):
        chart_container.loading = True   
        chart_container.objects = [get_temperature_plot(parameter_selector)]
        chart_container.loading = False 


    # ── Historical analysis card ──────────────────────────────
    historical_card = pn.Column(
        pn.pane.Markdown(
            "## 📈 Historical Data Analysis",
            styles={
                "font-family": "'DM Sans', sans-serif",
                "color": "#2D2F3E",
                "margin-bottom": "4px",
            },
        ),
        pn.pane.Markdown(
            "Select locations, a parameter, and a date range to explore sensor history.",
            styles={"color": "#7B82B4", "font-size": "13px", "margin-bottom": "16px"},
        ),
        pn.Row(
            pn.Column(
                pn.pane.Markdown(
                    "**Locations**",
                    styles={"color": "#5A5F94", "font-size": "11px", "text-transform": "uppercase",
                            "letter-spacing": "0.06em", "margin-bottom": "6px"},
                ),
                location_selector,
                sizing_mode='stretch_width',
            ),
            pn.Column(
                pn.pane.Markdown(
                    "**Parameter**",
                    styles={"color": "#5A5F94", "font-size": "11px", "text-transform": "uppercase",
                            "letter-spacing": "0.06em", "margin-bottom": "6px"},
                ),
                parameter_selector,
                sizing_mode='stretch_width',
            ),
            pn.Column(
                date_range_picker,
                sizing_mode='stretch_width',
            ),
            sizing_mode='stretch_width',
            styles={'gap': '24px', 'flex-wrap': 'wrap', 'align-items': 'flex-start'},
        ),
        pn.layout.Divider(),
        chart_container,
        styles=card_style,
        sizing_mode='stretch_width',
    )

    # ── Map card ──────────────────────────────────────────────
    map_card = pn.Column(
        pn.pane.Markdown(
            "## 🗺 Live Sensor Map",
            styles={
                "font-family": "'DM Sans', sans-serif",
                "color": "#2D2F3E",
                "margin-bottom": "12px",
            },
        ),
        filter_card,
        get_map,
        styles={**card_style, "background": "#FFFFFF"},
        sizing_mode='stretch_width',
    )

    infographic_container = pn.Column(
        pn.pane.Markdown("Selectează datele de mai sus și așteaptă încărcarea pentru a genera raportul.", styles={"color": "#7B82B4"}),
        sizing_mode='stretch_width',
        align='center'
    )

    @pn.depends(chart_trigger.param.value, parameter_selector.param.value, watch=True)
    def update_infographic(c, parameter_selector):
        global df_api_data
        if not df_api_data.empty:
            param_col = "temperature"
            if parameter_selector == 'Humidity': param_col = "humidity"
            if parameter_selector == 'Carbon Monoxide': param_col = "pm25"
            
            infographic_container.objects = [create_social_media_card(df_api_data, param_col)]
        else:
             infographic_container.objects = [pn.pane.Markdown("Nu sunt date suficiente.", styles={"color": "#7B82B4"})]

    report_card = pn.Column(
        pn.pane.Markdown("## 📱 Raport Social Media", styles={"font-family": "'DM Sans', sans-serif", "color": "#2D2F3E"}),
        infographic_container,
        styles=card_style,
    )

    # ── Forecast (XGBoost) section ────────────────────────────
    forecast_hours_slider = pn.widgets.IntSlider(
        name='Ore de predicție',
        start=6, end=72, step=6, value=24,
        bar_color='#A78BFA',
        stylesheets=["""
        :host { font-family: 'DM Sans', sans-serif !important; }
        label { font-size: 12px !important; color: #5A5F94 !important;
                font-weight: 600 !important; letter-spacing: 0.04em !important; }
        """],
    )

    forecast_btn = pn.widgets.Button(
        name='Generează Forecast',
        button_type='primary',
        width=200,
        stylesheets=["""
        :host button {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #A78BFA 0%, #7C3AED 100%) !important;
            color: #fff !important;
            border: none !important;
            padding: 10px 20px !important;
            cursor: pointer !important;
            transition: opacity 0.18s !important;
            box-shadow: 0 4px 14px rgba(167, 139, 250, 0.35) !important;
        }
        :host button:hover { opacity: 0.88 !important; }
        """],
    )

    forecast_container = pn.Column(
        pn.pane.HTML(
            """
            <div style="text-align:center; padding:40px 0; color:#7B82B4;
                        font-family:'DM Sans',sans-serif; font-size:14px;">
                <div style="font-size:36px; margin-bottom:10px;">🔮</div>
                Selectează date istorice și apasă <b>Generează Forecast</b><br>
                pentru a vedea predicțiile XGBoost.
            </div>
            """,
            sizing_mode='stretch_width',
        ),
        sizing_mode='stretch_width',
        min_height=200,
    )

    def _build_forecast_chart(hist_df, forecast_df, param, param_label, unit):
        """Build a layered Altair chart: historical + forecast + confidence band."""
        # Last 48h of historical data for context
        hist = hist_df[["timestamp", param]].copy()
        hist["timestamp"] = pd.to_datetime(hist["timestamp"])
        cutoff = hist["timestamp"].max() - pd.Timedelta(hours=48)
        hist = hist[hist["timestamp"] >= cutoff].copy()
        hist = hist.rename(columns={param: "value"})
        hist["type"] = "Istoric"

        fc = forecast_df.rename(columns={"forecast": "value"}).copy()
        fc["type"] = "Predicție"

        combined = pd.concat([hist, fc], ignore_index=True)

        # Confidence band (±10%)
        band_df = fc.copy()
        band_df["upper"] = band_df["value"] * 1.10
        band_df["lower"] = band_df["value"] * 0.90

        axis_cfg = dict(
            labelFont='DM Sans', titleFont='DM Sans',
            labelColor='#7B82B4', titleColor='#5A5F94',
            gridColor='#F0F2FA', domainColor='#E0E4F5',
        )

        # Historical line
        hist_line = alt.Chart(combined[combined["type"] == "Istoric"]).mark_line(
            strokeWidth=2.5,
            point=alt.OverlayMarkDef(filled=True, size=40),
        ).encode(
            x=alt.X('timestamp:T', title='Time', axis=alt.Axis(format='%d %b %H:%M', **axis_cfg)),
            y=alt.Y('value:Q', title=f'{param_label} ({unit})', axis=alt.Axis(**axis_cfg)),
            color=alt.value('#7C9EFF'),
            tooltip=[
                alt.Tooltip('timestamp:T', format='%Y-%m-%d %H:%M'),
                alt.Tooltip('value:Q', format='.1f', title=param_label),
            ],
        )

        # Forecast line (dashed)
        fc_line = alt.Chart(combined[combined["type"] == "Predicție"]).mark_line(
            strokeDash=[6, 4], strokeWidth=2.5,
            point=alt.OverlayMarkDef(filled=True, size=40),
        ).encode(
            x='timestamp:T',
            y='value:Q',
            color=alt.value('#F59E0B'),
            tooltip=[
                alt.Tooltip('timestamp:T', format='%Y-%m-%d %H:%M'),
                alt.Tooltip('value:Q', format='.1f', title='Predicție'),
            ],
        )

        # Confidence band
        band = alt.Chart(band_df).mark_area(opacity=0.15).encode(
            x='timestamp:T',
            y='lower:Q',
            y2='upper:Q',
            color=alt.value('#F59E0B'),
        )

        # Vertical line at forecast start
        fc_start_ts = fc["timestamp"].min()
        rule_df = pd.DataFrame({"x": [fc_start_ts]})
        rule = alt.Chart(rule_df).mark_rule(
            strokeDash=[4, 4], strokeWidth=1.5, color='#A78BFA'
        ).encode(x='x:T')

        # Legend entries (manual)
        legend_data = pd.DataFrame({
            "label": ["Istoric", "Predicție XGBoost"],
            "color": ["#7C9EFF", "#F59E0B"],
        })
        legend = alt.Chart(legend_data).mark_point(size=0).encode(
            color=alt.Color('label:N',
                scale=alt.Scale(domain=["Istoric", "Predicție XGBoost"],
                                range=["#7C9EFF", "#F59E0B"]),
                legend=alt.Legend(title="Tip", titleFont='DM Sans', labelFont='DM Sans',
                                  titleColor='#5A5F94', labelColor='#2D2F3E')),
        )

        chart = (
            alt.layer(hist_line, band, fc_line, rule, legend)
            .properties(
                title=alt.TitleParams(
                    f'🔮 Forecast {param_label} — următoarele {len(fc)} ore',
                    font='DM Sans', fontSize=15, fontWeight=600,
                    color='#2D2F3E', anchor='start', offset=8,
                ),
                height=400,
                width='container',
                background='#FFFFFF',
            )
            .configure_view(strokeWidth=0)
            .interactive()
        )
        return chart

    def on_forecast_click(event):
        global df_api_data
        forecast_container.loading = True

        try:
            if df_api_data is None or df_api_data.empty:
                forecast_container.objects = [
                    pn.pane.HTML(
                        '<div style="text-align:center;padding:30px;color:#EF4444;'
                        'font-family:DM Sans,sans-serif;">'
                        '⚠️ Nu există date încărcate. Selectează locații și un interval de date mai întâi.</div>',
                        sizing_mode='stretch_width',
                    )
                ]
                return

            param_sel = parameter_selector.value
            param_col = "temperature"
            param_label = "Temperatură"
            unit = "°C"
            if param_sel == "Humidity":
                param_col = "humidity"
                param_label = "Umiditate"
                unit = "%"
            elif param_sel == "Carbon Monoxide":
                param_col = "pm25"
                param_label = "PM2.5"
                unit = "µg/m³"

            horizon = forecast_hours_slider.value
            fc_df = train_and_forecast(df_api_data, param_col, horizon)

            if fc_df.empty:
                forecast_container.objects = [
                    pn.pane.HTML(
                        '<div style="text-align:center;padding:30px;color:#F59E0B;'
                        'font-family:DM Sans,sans-serif;">'
                        '⚠️ Date insuficiente pentru forecast. Te rugăm să selectezi un interval de <b>minim 2-3 zile</b> de istoric din selectorul de date.</div>',
                        sizing_mode='stretch_width',
                    )
                ]
                return

            chart = _build_forecast_chart(df_api_data, fc_df, param_col, param_label, unit)

            # Stats summary bar
            fc_mean = fc_df["forecast"].mean()
            fc_min  = fc_df["forecast"].min()
            fc_max  = fc_df["forecast"].max()
            stats_html = f"""
            <div style="display:flex; gap:16px; flex-wrap:wrap; margin-top:12px; font-family:'DM Sans',sans-serif;">
                <div style="flex:1; min-width:140px; background:#F5F3FF; border-radius:12px;
                            padding:14px 18px; border-left:4px solid #A78BFA;">
                    <div style="font-size:11px; color:#7B82B4; text-transform:uppercase; letter-spacing:0.05em;">Media Predicție</div>
                    <div style="font-size:20px; font-weight:700; color:#7C3AED;">{fc_mean:.1f} {unit}</div>
                </div>
                <div style="flex:1; min-width:140px; background:#EFF6FF; border-radius:12px;
                            padding:14px 18px; border-left:4px solid #7C9EFF;">
                    <div style="font-size:11px; color:#7B82B4; text-transform:uppercase; letter-spacing:0.05em;">Minim Predicție</div>
                    <div style="font-size:20px; font-weight:700; color:#3B82F6;">{fc_min:.1f} {unit}</div>
                </div>
                <div style="flex:1; min-width:140px; background:#FFF7ED; border-radius:12px;
                            padding:14px 18px; border-left:4px solid #F59E0B;">
                    <div style="font-size:11px; color:#7B82B4; text-transform:uppercase; letter-spacing:0.05em;">Maxim Predicție</div>
                    <div style="font-size:20px; font-weight:700; color:#D97706;">{fc_max:.1f} {unit}</div>
                </div>
            </div>
            """

            forecast_container.objects = [
                pn.pane.Vega(chart, sizing_mode='stretch_width'),
                pn.pane.HTML(stats_html, sizing_mode='stretch_width'),
            ]

        except Exception as e:
            forecast_container.objects = [
                pn.pane.HTML(
                    f'<div style="text-align:center;padding:30px;color:#EF4444;'
                    f'font-family:DM Sans,sans-serif;">'
                    f'❌ Eroare la generarea forecast-ului: {e}</div>',
                    sizing_mode='stretch_width',
                )
            ]
        finally:
            forecast_container.loading = False

    forecast_btn.on_click(on_forecast_click)

    forecast_card = pn.Column(
        pn.pane.Markdown(
            "## 🔮 Forecast (XGBoost)",
            styles={"font-family": "'DM Sans', sans-serif", "color": "#2D2F3E", "margin-bottom": "4px"},
        ),
        pn.pane.Markdown(
            "Predicție bazată pe datele istorice folosind XGBoost. Selectează orizontul de timp și apasă butonul.",
            styles={"color": "#7B82B4", "font-size": "13px", "margin-bottom": "16px"},
        ),
        pn.Row(
            forecast_hours_slider,
            forecast_btn,
            sizing_mode='stretch_width',
            styles={'gap': '20px', 'align-items': 'flex-end', 'flex-wrap': 'wrap'},
        ),
        pn.layout.Divider(),
        forecast_container,
        styles=forecast_card_style,
        sizing_mode='stretch_width',
    )

    # ── AI Chat section ───────────────────────────────────────
    pn.config.raw_css.append(chat_bubble_css)

    chat_agent = ChatAgent()

    chat_input = pn.widgets.TextInput(
        name='',
        placeholder='Pune o întrebare despre datele din senzori...',
        sizing_mode='stretch_width',
        stylesheets=["""
        :host { font-family: 'DM Sans', sans-serif !important; }
        .bk-input {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 14px !important;
            color: #2D2F3E !important;
            border: 1.5px solid #E0E4F5 !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            background: #F7F8FC !important;
            transition: border-color 0.2s !important;
        }
        .bk-input:focus {
            border-color: #34D399 !important;
            background: #fff !important;
            box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.15) !important;
        }
        """],
    )

    chat_send_btn = pn.widgets.Button(
        name='Trimite',
        button_type='primary',
        width=120,
        stylesheets=["""
        :host button {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            background: linear-gradient(135deg, #34D399 0%, #059669 100%) !important;
            color: #fff !important;
            border: none !important;
            padding: 12px 20px !important;
            cursor: pointer !important;
            transition: opacity 0.18s !important;
            box-shadow: 0 4px 14px rgba(52, 211, 153, 0.3) !important;
        }
        :host button:hover { opacity: 0.88 !important; }
        """],
    )

    chat_reset_btn = pn.widgets.Button(
        name='🗑',
        button_type='light',
        width=44,
        stylesheets=["""
        :host button {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 16px !important;
            border-radius: 12px !important;
            background: #F7F8FC !important;
            border: 1.5px solid #E0E4F5 !important;
            color: #7B82B4 !important;
            padding: 10px !important;
            cursor: pointer !important;
            transition: all 0.18s !important;
        }
        :host button:hover {
            border-color: #FCA5A5 !important;
            background: #FEF2F2 !important;
            color: #EF4444 !important;
        }
        """],
    )

    welcome_html = """
    <div class="chat-history" id="chat-history">
        <div class="chat-bubble assistant">
            👋 Salut! Sunt asistentul tău AI pentru calitatea aerului din Sibiu.<br><br>
            Poți să mă întrebi orice despre datele din senzori, de exemplu:<br>
            • <i>"Care e temperatura medie în Centru?"</i><br>
            • <i>"Când a fost cel mai poluat aer?"</i><br>
            • <i>"Compară umiditatea din Gusterița cu Caposu"</i>
        </div>
    </div>
    """

    chat_history_pane = pn.pane.HTML(
        welcome_html,
        sizing_mode='stretch_width',
    )

    def _render_chat_history(history):
        """Render conversation history as HTML chat bubbles."""
        if not history:
            return welcome_html

        html = '<div class="chat-history" id="chat-history">'
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            # Basic markdown-like formatting
            content = content.replace("\n", "<br>")
            # Bold: **text** → <b>text</b>
            import re
            content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
            # Code: `text` → <code>text</code>
            content = re.sub(r'`([^`]+)`', r'<code style="background:#E0E4F5;padding:2px 6px;border-radius:4px;font-size:12px;">\1</code>', content)

            css_class = "user" if role == "user" else "assistant"
            html += f'<div class="chat-bubble {css_class}">{content}</div>'
        html += '</div>'

        # Auto-scroll to bottom
        html += """
        <script>
            setTimeout(function() {
                var el = document.getElementById('chat-history');
                if (el) el.scrollTop = el.scrollHeight;
            }, 100);
        </script>
        """
        return html

    def _on_chat_send(event):
        question = chat_input.value.strip()
        if not question:
            return

        # Show user message immediately
        chat_agent.history.append({"role": "user", "content": question})
        # Remove the appended user message since ask() will add it again
        chat_agent.history.pop()

        chat_input.value = ''

        # Show loading state
        loading_html = _render_chat_history(chat_agent.get_history() + [{"role": "user", "content": question}])
        loading_html = loading_html.replace(
            '</div>\n        <script>',
            '<div class="chat-loading"><span></span><span></span><span></span></div></div>\n        <script>'
        )
        chat_history_pane.object = loading_html

        # Get answer from AI
        answer = chat_agent.ask(question)

        # Update chat
        chat_history_pane.object = _render_chat_history(chat_agent.get_history())

    def _on_chat_reset(event):
        chat_agent.reset()
        chat_history_pane.object = welcome_html

    # Handle Enter key submit
    chat_input.param.watch(lambda event: _on_chat_send(event) if event.new and event.new.endswith('\n') else None, 'value')
    chat_send_btn.on_click(_on_chat_send)
    chat_reset_btn.on_click(_on_chat_reset)

    chat_card = pn.Column(
        pn.Row(
            pn.pane.Markdown(
                "## 💬 Asistent AI",
                styles={"font-family": "'DM Sans', sans-serif", "color": "#2D2F3E", "margin-bottom": "0px"},
            ),
            pn.Spacer(),
            chat_reset_btn,
            sizing_mode='stretch_width',
            styles={'align-items': 'center'},
        ),
        pn.pane.Markdown(
            "Pune întrebări în limbaj natural despre datele din senzori. AI-ul generează interogări SQL automat.",
            styles={"color": "#7B82B4", "font-size": "13px", "margin-bottom": "12px"},
        ),
        pn.layout.Divider(),
        chat_history_pane,
        pn.Row(
            chat_input,
            chat_send_btn,
            sizing_mode='stretch_width',
            styles={'gap': '10px', 'align-items': 'flex-end', 'margin-top': '12px'},
        ),
        styles=chat_card_style,
        sizing_mode='stretch_width',
    )

    # ── Page header ───────────────────────────────────────────
    header = pn.pane.Markdown(
        # """
        # # 🌿 Air Quality Dashboard
        # Real-time environmental monitoring — Sibiu & surroundings
        # """,
        styles={
            "font-family": "'DM Sans', sans-serif",
            "color": "#2D2F3E",
            "border-bottom": "2px solid #EEF0FA",
            "padding-bottom": "16px",
            "margin-bottom": "20px",
        },
        sizing_mode='stretch_width',
    )

    # ── Root layout ───────────────────────────────────────────
    layout = pn.Column(
        render_navbar(active="dashboard", title="🌿 **Urban Bike Data**"),
        counter,
        chart_trigger,
        header,
        map_card,
        historical_card,
        # report_card,
        forecast_card,
        chat_card,
        sizing_mode='stretch_width',
        styles={
            "max-width": "1280px",
            "margin": "0 auto",
            "padding": "24px 20px",
            "background": "#F7F8FC",
        },
    )

    return layout


# ── Admin page ────────────────────────────────────────────────
def render_admin_page():
    pn.extension('tabulator')
    pn.config.raw_css.append(FONT_IMPORT + global_style)

    upload_widget = pn.widgets.FileInput(accept='.xlsx', name='Upload Excel')

    admin_btn = pn.widgets.Button(
        name='← Back to Dashboard',
        button_type='light',
        width=180,
        stylesheets=["""
        :host button {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: 1.5px solid #A5B4FC !important;
            background: #FFFFFF !important;
            color: #4B51A0 !important;
            padding: 8px 16px !important;
            cursor: pointer !important;
            transition: all 0.18s !important;
        }
        :host button:hover {
            background: #EEF0FF !important;
        }
        """],
    )
    admin_btn.js_on_click(code="window.location.href = '/dashboard'")

    @pn.depends(upload_widget.param.value)
    def process_excel(file_content):
        if file_content is None:
            return pn.pane.Markdown(
                "📂 Upload an Excel file to preview its data.",
                styles={"color": "#7B82B4", "padding": "40px 0", "text-align": "center"},
            )
        try:
            import io
            df = pd.read_excel(io.BytesIO(file_content))
            return pn.widgets.Tabulator(
                df,
                pagination='remote',
                page_size=10,
                height=400,
                stylesheets=["""
                .tabulator {
                    font-family: 'DM Mono', monospace !important;
                    font-size: 13px !important;
                    border: none !important;
                    border-radius: 10px !important;
                    overflow: hidden;
                }
                .tabulator-header {
                    background: #F0F2FF !important;
                    border-bottom: 2px solid #E0E4F5 !important;
                }
                .tabulator-header .tabulator-col {
                    background: transparent !important;
                    color: #5A5F94 !important;
                    font-weight: 600 !important;
                    font-size: 11px !important;
                    text-transform: uppercase !important;
                    letter-spacing: 0.05em !important;
                }
                .tabulator-row {
                    border-bottom: 1px solid #EEF0FA !important;
                    background: #FFFFFF !important;
                }
                .tabulator-row:hover {
                    background: #F7F8FF !important;
                }
                """],
            )
        except Exception as e:
            return pn.pane.Alert(f"Error reading file: {str(e)}", alert_type='danger')

    layout = pn.Column(
        pn.pane.Markdown(
            "# 🗂 Admin Panel",
            styles={"font-family": "'DM Sans', sans-serif", "color": "#2D2F3E"},
        ),
        admin_btn,
        pn.layout.Divider(),
        pn.Column(
            upload_widget,
            pn.layout.Divider(),
            process_excel,
            styles=card_style,
            sizing_mode='stretch_width',
        ),
        sizing_mode='stretch_width',
        styles={"max-width": "960px", "margin": "0 auto", "padding": "32px 20px", "background": "#F7F8FC"},
    )

    return layout