import os
import sys
import requests
import pandas as pd
from datetime import datetime
from dateutil import tz
import pytz
import phonenumbers
from phonenumbers import geocoder

# -------- Config ----------
API_VERSION = os.getenv("WA_API_VERSION", "v21.0")
PHONE_NUMBER_ID = os.getenv("WABA_PHONE_NUMBER_ID")
META_TOKEN = os.getenv("META_WA_TOKEN")
SENDER_NAME = os.getenv("SENDER_NAME", "Un amigo")

EVENTS_PATH = os.path.join(os.path.dirname(__file__), "events.csv")

TEMPLATE_BY_TYPE = {
    "cumple": "feliz_cumple",
    "santo":  "feliz_santo"
}

# margen de envío: si el job corre cada 10 minutos, aceptamos 09:00-09:09
SEND_WINDOW_MINUTES = set(range(0, 10))

# Para países con múltiples zonas horarias, podemos fijar una por defecto:
COUNTRY_DEFAULT_TZ = {
    "US": "America/New_York",
    "CA": "America/Toronto",
    "AU": "Australia/Sydney",
    "BR": "America/Sao_Paulo",
    "MX": "America/Mexico_City",
    "RU": "Europe/Moscow",
    "CN": "Asia/Shanghai",
    "IN": "Asia/Kolkata"
}

def parse_tz_from_phone(phone_e164: str):
    \"\"\"Inferir zona horaria por prefijo (aproximación).
    1) Obtener país (ej. 'ES', 'US') con libphonenumber.
    2) Si el país tiene una única tz en pytz, usarla.
    3) Si tiene varias, usar COUNTRY_DEFAULT_TZ si está definida.
    4) Si no, usar la primera de la lista de pytz (suele ser capital).
    \"\"\"
    try:
        num = phonenumbers.parse("+" + phone_e164 if not phone_e164.startswith("+") else phone_e164, None)
        region = geocoder.region_code_for_number(num)
        if not region:
            return None
        tz_list = pytz.country_timezones.get(region, [])
        if not tz_list:
            return None
        if len(tz_list) == 1:
            return tz_list[0]
        if region in COUNTRY_DEFAULT_TZ:
            return COUNTRY_DEFAULT_TZ[region]
        return tz_list[0]
    except Exception:
        return None

def local_now(tz_name: str):
    timezone = tz.gettz(tz_name)
    if timezone is None:
        timezone = tz.gettz("UTC")
    return datetime.now(tz=timezone)

def is_today_for_event(date_str: str, event_type: str, local_dt: datetime):
    try:
        if event_type == "santo" and date_str.startswith("----"):
            mm_dd = date_str[-5:]  # "MM-DD"
            return f\"{local_dt.month:02d}-{local_dt.day:02d}\" == mm_dd
        else:
            dt = datetime.fromisoformat(date_str)
            return (dt.month, dt.day) == (local_dt.month, local_dt.day)
    except Exception:
        return False

def within_local_window(local_dt: datetime, target_hour=9):
    return local_dt.hour == target_hour and local_dt.minute in SEND_WINDOW_MINUTES

def send_template_message(to_phone_e164: str, template_name: str, lang_code: str, params: list[str]):
    url = f\"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages\"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone_e164 if to_phone_e164.startswith("+") else f"+{to_phone_e164}",
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang_code},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type":"text","text": p} for p in params]
                }
            ]
        }
    }
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    ok = r.status_code < 300
    print(f"[{'OK' if ok else 'ERROR'}] {to_phone_e164} -> {template_name} ({lang_code}) {r.status_code}")
    if not ok:
        print(r.text)
    return ok

def load_events():
    if not os.path.exists(EVENTS_PATH):
        print(f"[ERROR] No existe {EVENTS_PATH}")
        sys.exit(1)
    df = pd.read_csv(EVENTS_PATH, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"name","phone","event_type","date","lang","tz"}
    if not required.issubset(set(df.columns)):
        print("[ERROR] events.csv debe tener columnas: name, phone, event_type, date, lang, tz")
        sys.exit(1)
    return df.applymap(lambda x: x.strip())

def run():
    # Cargamos contactos
    df = load_events()

    total_candidates = 0
    total_sent = 0

    for _, row in df.iterrows():
        name = row["name"]
        phone = row["phone"]
        etype = row["event_type"].lower()
        date_str = row["date"]
        lang = (row["lang"] or "es").lower()
        tz_name = row["tz"]

        if not phone or not date_str or etype not in TEMPLATE_BY_TYPE:
            continue

        # Resolver zona horaria
        if not tz_name:
            tz_name = parse_tz_from_phone(phone) or "UTC"

        now_local = local_now(tz_name)

        # Comprobar si hoy es su día y si estamos en la ventana 09:00-09:09 locales
        if is_today_for_event(date_str, etype, now_local) and within_local_window(now_local, target_hour=9):
            total_candidates += 1
            template = TEMPLATE_BY_TYPE[etype]
            params = [name, SENDER_NAME]
            ok = send_template_message(phone, template, lang, params)
            if ok:
                total_sent += 1

    print(f"Contactos elegibles: {total_candidates} | Enviados: {total_sent}")

if __name__ == "__main__":
    run()
