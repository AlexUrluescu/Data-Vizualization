import panel as pn
import threading
import folium

def create_app():
    # --- WIDGETS (Inputs) ---
    # See: https://panel.holoviz.org/reference/index.html#widgets
    title_input = pn.widgets.TextInput(name='Title', value='My Dashboard')
    slider = pn.widgets.IntSlider(name='Select a Number', start=1, end=100, value=50)
    color_picker = pn.widgets.ColorPicker(name='Pick a Color', value='#007bff')

    m = folium.Map(location=[52.51, 13.39], zoom_start=12)

    folium_pane = pn.pane.plot.Folium(m, height=400)



    # --- PANES (Outputs) ---
    # See: https://panel.holoviz.org/reference/index.html#panes
    # We bind the output to the widgets so it updates automatically
    @pn.depends(slider, color_picker)
    def update_result(val, color):
            return pn.pane.Markdown(
                f"# You selected: {val}", 
            
                styles={'color': color, 'font-family': 'Arial'}
            )

    # --- LAYOUT (Arrangement) ---
    # See: https://panel.holoviz.org/reference/index.html#layouts
    # We organize components into Rows and Columns
    layout = pn.Column(
        pn.Row(title_input, color_picker),
        slider,
        folium_pane,
        
        pn.layout.Divider(),
        
        update_result
    )
    
    return layout       

def run_panel_server():
    pn.serve(
        {'/dashboard': create_app}, 
        port=5006, 
        allow_websocket_origin=["127.0.0.1:5000", "127.0.0.1:5001"], 
        show=False,
        loop=None
    )

t = threading.Thread(target=run_panel_server, daemon=True)
t.start()