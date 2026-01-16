date_picker_style = """
/* Stilizăm input-ul propriu-zis (căsuța unde scrie data) */
:host(.my-date-picker) input.bk-input {
    background-color: #f0f4f8;      /* Același gri ca la radio buttons */
    border: 1px solid #d1d9e6;      /* Același border */
    border-radius: 20px;            /* Rotunjire mare (pill shape) */
    padding: 6px 15px;
    font-size: 14px;
    color: #444;
    text-align: center;             /* Text centrat */
    transition: all 0.2s ease;
    min-height: 35px;               /* Înălțime fixă pentru consistență */
    max-width: 30%;
}

/* Efect la hover */
:host(.my-date-picker) input.bk-input:hover {
    background-color: #e2e6ea;
    border-color: #adb5bd;
}

/* Efect când dai click (focus) */
:host(.my-date-picker) input.bk-input:focus {
    border-color: #0072b5;          /* Albastru la activare */
    box-shadow: 0 0 0 3px rgba(0,114,181,0.2);
}

/* Stilizăm eticheta de deasupra (titlul "Date Range Picker") */
:host(.my-date-picker) label.bk-input-group-label {
    font-size: 12px;
    font-weight: bold;
    color: #666;
    margin-bottom: 5px;
    margin-left: 10px; /* Aliniem cu rotunjimea inputului */
}
"""

my_custom_style = """
:host(.location-selector) .bk-input-group {
    display: flex;
    gap: 8px; /* Spațiu între butoane */
    flex-wrap: wrap;
}



/* Stilizăm label-ul (butonul vizibil) */
:host(.location-selector) label {
    background-color: #f0f4f8;
    border: 1px solid #d1d9e6;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 14px;
    color: #444;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: center;
    margin: 0 !important; /* Panel adaugă uneori margini default */
}

/* Hover */
:host(.location-selector) label:hover {
    background-color: #e2e6ea;
    border-color: #adb5bd;
}

/* Când este selectat - folosim pseudo-clasa :has sau logica internă */
/* NOTA: Panel pune clasa 'active' pe label în versiunile noi */
:host(.location-selector) label.active, 
:host(.location-selector) input:checked + label {
    background-color: #0072b5 !important;
    color: white !important;
    border-color: #0072b5 !important;
    box-shadow: 0 2px 4px rgba(0,114,181,0.3);
}
"""


checkbox_style_square = """
/* 1. Resetăm stilul default al browserului pentru input */
:host(.styled-checkbox) input[type="checkbox"] {
    appearance: none;           /* Ștergem stilul nativ */
    -webkit-appearance: none;
    width: 20px;                /* Dimensiune mai mare */
    height: 20px;
    border: 2px solid #b0b8c4;  /* Bordură gri elegantă */
    border-radius: 4px;         /* Colțuri ușor rotunjite (nu cerc) */
    background-color: white;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
    position: relative;
    vertical-align: middle;
    margin-right: 8px;          /* Spațiu până la text */
}

/* 2. Hover - Când treci cu mouse-ul peste pătrățel */
:host(.styled-checkbox) input[type="checkbox"]:hover {
    border-color: #0072b5;      /* Se face albastru la contur */
    background-color: #f0f8ff;  /* Un albastru foarte palid fundal */
}

/* 3. Checked - Când este bifat */
:host(.styled-checkbox) input[type="checkbox"]:checked {
    background-color: #0072b5;  /* Pătrățelul devine plin albastru */
    border-color: #0072b5;
}

/* 4. Desenăm "bifa" (checkmark-ul alb) în interior */
:host(.styled-checkbox) input[type="checkbox"]:checked::after {
    content: '';
    position: absolute;
    left: 6px;
    top: 2px;
    width: 5px;
    height: 10px;
    border: solid white;
    border-width: 0 2px 2px 0;  /* Desenăm L-ul care formează bifa */
    transform: rotate(45deg);
}

/* 5. Stilizăm textul de lângă (Label) */
:host(.styled-checkbox) span {
    font-size: 14px;
    color: #333;
    font-weight: 500;
    vertical-align: middle;
    cursor: pointer;
}
"""
