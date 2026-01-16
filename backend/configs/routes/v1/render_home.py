import os
from flask import Blueprint, render_template, request
from configs.config import Config
from bokeh.embed import server_document

render_home_page = Blueprint("render_home_page", __name__)

@render_home_page.route("/", methods=["GET"])
def index():
    # 1. Check if we are on Render (Production)
    render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    
    if render_hostname:
        # Production: Use the secure HTTPS Render URL
        dashboard_url = f"https://{render_hostname}/dashboard"
    else:
        # Localhost: Use the local URL (assuming port 5001)
        dashboard_url = "http://127.0.0.1:5001/dashboard"

    # 2. Generate the script tag pointing to the correct URL
    script = server_document(dashboard_url)
    
    return render_template('index.html', panel_script=script)