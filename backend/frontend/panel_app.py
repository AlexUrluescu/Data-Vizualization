import panel as pn
import threading
import folium
import altair as alt
import pandas as pd
import io
import datetime as dt


def render_dashboard_page():
    # --- WIDGETS (Inputs) ---
    # See: https://panel.holoviz.org/reference/index.html#widgets
    pn.extension('vega')
    admin_btn = pn.widgets.Button(name='Go to Admin', button_type='primary', width=100)
    admin_btn.js_on_click(code="window.location.href = '/admin'")

    title_input = pn.widgets.TextInput(name='Title', value='My Dashboard')
    datetime_picker = pn.widgets.DatetimePicker(
    name='Datetime Picker', value=dt.datetime(2021, 3, 2, 12, 10)
)

    m = folium.Map(location=[45.7983, 24.1256], zoom_start=12)

    folium_pane = pn.pane.plot.Folium(m, height=400)

    data = {
        'An': [2013, 2014, 2015, 2016, 2017, 2018, 
                 2019, 2020, 2021, 2022, 2023, 2024],
        'Populatie': [1000, 1200, 1500, 1800, 2200, 2100, 2500, 3000, 3200, 3300, 3350, 3500]
    }
    df = pd.DataFrame(data)

    chart = alt.Chart(df).mark_area(
        line={'color':'darkblue'},
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='white', offset=0),
                   alt.GradientStop(color='darkblue', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X('An:O', axis=alt.Axis(title='Anul', labelAngle=0)),
        y=alt.Y('Populatie', axis=alt.Axis(title='Locuitori')),
        tooltip=['An', 'Populatie']
    ).properties(
        width='container',
        height=400,
        title="Evoluția Populației (Anul 2024)"
    )

    # --- PANES (Outputs) ---
    # See: https://panel.holoviz.org/reference/index.html#panes
    # We bind the output to the widgets so it updates automatically

    # --- LAYOUT (Arrangement) ---
    # See: https://panel.holoviz.org/reference/index.html#layouts
    # We organize components into Rows and Columns
    layout = pn.Column(
        pn.Row(title_input),
        admin_btn,
        datetime_picker,
        folium_pane,
        pn.layout.Divider(),
        chart,
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