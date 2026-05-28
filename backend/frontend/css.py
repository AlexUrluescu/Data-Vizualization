
FONT_IMPORT = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600&family=DM+Mono:wght@400;500&display=swap');
"""

global_style = """
body {
    font-family: 'DM Sans', sans-serif !important;
    background: #F7F8FC !important;
    color: #2D2F3E !important;
}
:host, .bk-root {
    font-family: 'DM Sans', sans-serif !important;
    color: #2D2F3E !important;
}
"""

card_style = {
    "background": "#FFFFFF",
    "border-radius": "16px",
    "box-shadow": "0 2px 16px rgba(100, 108, 180, 0.08)",
    "padding": "20px 24px",
    "margin-bottom": "16px",
}

section_header_style = {
    "border-left": "4px solid #A5B4FC",
    "padding-left": "12px",
    "margin-bottom": "8px",
}

divider_style = """
.bk-Divider hr {
    border: none;
    border-top: 1.5px solid #EEF0FA;
    margin: 8px 0;
}
"""

date_picker_style = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&display=swap');

:host {
    font-family: 'DM Sans', sans-serif !important;
}

/* Container */
.bk-input-group {
    background: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1.5px solid #E0E4F5 !important;
    padding: 6px 10px !important;
    transition: border-color 0.2s;
}

.bk-input-group:focus-within {
    border-color: #A5B4FC !important;
    box-shadow: 0 0 0 3px rgba(165, 180, 252, 0.18) !important;
}

/* Text field */
.bk-input {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    color: #2D2F3E !important;
    background: transparent !important;
    border: none !important;
    outline: none !important;
}

/* Label */
label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #7B82B4 !important;
    margin-bottom: 4px !important;
}

/* Calendar popup */
.flatpickr-calendar {
    font-family: 'DM Sans', sans-serif !important;
    border-radius: 14px !important;
    border: none !important;
    box-shadow: 0 8px 32px rgba(100, 108, 180, 0.16) !important;
    background: #FFFFFF !important;
    padding: 8px !important;
}

.flatpickr-months {
    background: #F0F2FF !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 4px !important;
}

.flatpickr-current-month {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #4B51A0 !important;
}

.flatpickr-day.selected,
.flatpickr-day.selected:hover,
.flatpickr-day.startRange,
.flatpickr-day.endRange {
    background: #A5B4FC !important;
    border-color: #A5B4FC !important;
    color: #fff !important;
    font-weight: 600 !important;
}

.flatpickr-day.inRange {
    background: #EEF0FF !important;
    border-color: transparent !important;
    color: #4B51A0 !important;
}

.flatpickr-day:hover {
    background: #F0F2FF !important;
}

.flatpickr-weekday {
    color: #A5B4FC !important;
    font-size: 11px !important;
    font-weight: 600 !important;
}
"""

# ── RadioBoxGroup / CheckBoxGroup (parameter & location selectors) ──
my_custom_style = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');

:host {
    font-family: 'DM Sans', sans-serif !important;
}

label {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #7B82B4 !important;
    margin-bottom: 8px !important;
    display: block;
}

/* Pill chip styling for each option */
.bk-input-group {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
}

input[type="radio"],
input[type="checkbox"] {
    display: none !important;
}

input[type="radio"] + span,
input[type="checkbox"] + span {
    display: inline-flex !important;
    align-items: center !important;
    padding: 6px 14px !important;
    border-radius: 50px !important;
    border: 1.5px solid #D6D9F5 !important;
    background: #F7F8FC !important;
    color: #5A5F94 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    white-space: nowrap !important;
}

input[type="radio"]:checked + span,
input[type="checkbox"]:checked + span {
    background: #A5B4FC !important;
    border-color: #A5B4FC !important;
    color: #fff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(165, 180, 252, 0.35) !important;
}

input[type="radio"] + span:hover,
input[type="checkbox"] + span:hover {
    border-color: #A5B4FC !important;
    background: #EEF0FF !important;
    color: #4B51A0 !important;
}
"""

checkbox_style_square = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');

:host {
    font-family: 'DM Sans', sans-serif !important;
}

/* Hide native checkbox */
input[type="checkbox"] {
    display: none !important;
}

/* Custom toggle-chip */
input[type="checkbox"] + span {
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    padding: 7px 16px !important;
    border-radius: 10px !important;
    border: 1.5px solid #E0E4F5 !important;
    background: #FFFFFF !important;
    color: #5A5F94 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
}

input[type="checkbox"] + span::before {
    content: '' !important;
    width: 8px !important;
    height: 8px !important;
    border-radius: 50% !important;
    background: #D6D9F5 !important;
    flex-shrink: 0 !important;
    transition: background 0.18s !important;
}

input[type="checkbox"]:checked + span {
    background: #EEF6F0 !important;
    border-color: #86EFAC !important;
    color: #22543D !important;
    font-weight: 600 !important;
}

input[type="checkbox"]:checked + span::before {
    background: #4ADE80 !important;
}

input[type="checkbox"] + span:hover {
    border-color: #A5B4FC !important;
    background: #F7F8FF !important;
}
"""

map_container_style = {
    "border-radius": "16px",
    "overflow": "hidden",
    "box-shadow": "0 2px 16px rgba(100, 108, 180, 0.10)",
}

chart_container_style = {
    "background": "#FFFFFF",
    "border-radius": "16px",
    "padding": "20px",
    "box-shadow": "0 2px 16px rgba(100, 108, 180, 0.08)",
    "min-height": "320px",
}

def section_label(text: str, emoji: str = "") -> str:
    return f"### {emoji} {text}" if emoji else f"### {text}"

forecast_card_style = {
    "background": "#FFFFFF",
    "border-radius": "16px",
    "box-shadow": "0 2px 16px rgba(100, 108, 180, 0.08)",
    "padding": "20px 24px",
    "margin-bottom": "16px",
    "border-top": "3px solid #A78BFA",
}