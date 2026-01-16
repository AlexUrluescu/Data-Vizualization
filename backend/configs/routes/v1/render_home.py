from flask import Blueprint
from configs.config import Config
from bokeh.embed import server_document
import frontend.panel_app as panel_app
from flask import render_template

render_home_page = Blueprint("render_home_page", __name__)
db = Config.get_db()
cars_collection = db["cars"]
cities_collection = db["cities"]

@render_home_page.route("/", methods=["GET"])
def index():
    script = server_document('http://127.0.0.1:5006/dashboard')
    return render_template('index.html', panel_script=script)