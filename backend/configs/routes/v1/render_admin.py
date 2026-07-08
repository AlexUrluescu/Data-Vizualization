from flask import Blueprint
from bokeh.embed import server_document
from flask import render_template

render_admin_page = Blueprint("render_admin_page", __name__)

@render_admin_page.route("/", methods=["GET"])
def index():
    script = server_document('http://127.0.0.1:5006/admin')
    return render_template('index.html', panel_script=script)