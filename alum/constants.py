import orjson

ORJSON_OPTIONS = orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS

# Date in Indonesia
DAY_INDO = {
    "monday": "senin",
    "tuesday": "selasa",
    "wednesday": "rabu",
    "thursday": "kamis",
    "friday": "jumat",
    "saturday": "sabtu",
    "sunday": "minggu",
}
MONTH_INDO = {
    "january": "januari",
    "february": "februari",
    "march": "maret",
    "april": "april",
    "may": "mei",
    "june": "juni",
    "july": "juli",
    "august": "agustus",
    "september": "september",
    "october": "oktober",
    "november": "november",
    "december": "desember",
}

# Time format
TIME_FORMAT = "%d/%m/%Y, %H:%M:%S"

# Style
BLUE_1 = "#283593"
BLUE_2 = "#3F51B5"
YELLOW = "#FFD54F"
GREEN_1 = "#2E7D32"
GREEN_2 = "#388E3C"
RED_1 = "#E53935"
RED_2 = "#D32F2F"

# Stylesheet
RED_BTN_QSS = f"""
    QPushButton {{
        background-color: { RED_1 };
        color: white;
        border: none;
    }}
    QPushButton:hover:!pressed {{
        background-color: { RED_2 };
    }}
"""
GREEN_BTN_QSS = f"""
    QPushButton {{
        background: { GREEN_1 };
        color: white;
        border: none;
    }}
    QPushButton:hover:!pressed {{
        background: { GREEN_2 };
    }}
"""
