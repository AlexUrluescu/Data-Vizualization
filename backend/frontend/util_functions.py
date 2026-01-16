import datetime as dt


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