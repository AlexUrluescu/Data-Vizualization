import os
from flask import Blueprint, redirect

render_home_page = Blueprint("render_home_page", __name__)

@render_home_page.route("/", methods=["GET"])
def index():
    return redirect("/dashboard")