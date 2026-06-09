from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from geopy.geocoders import Nominatim
import pandas as pd
import joblib
import lightgbm as lgb
import numpy as np
import requests
import geocoder
import os
from datetime import datetime, date
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =========================
# TELEGRAM CONFIG
# =========================
import serial

ESP32_PORT = "COM3"   # change if needed
ESP32_BAUD = 115200

BOT_TOKEN = "8200554064:AAFcZtgyIsTK_CUw9WQXkz1OTm30kqxRus8"
CHAT_ID = "-1003683765096"



###ESP 32 SIDE
def send_alert_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print("📨 Telegram alert sent")
        else:
            print("❌ Telegram error:", r.text)
    except Exception as e:
        print("❌ Telegram exception:", e)

def send_buzzer_command(command):
    try:
        ser = serial.Serial(ESP32_PORT, ESP32_BAUD, timeout=2)
        time.sleep(2)
        ser.write((command + "\n").encode())
        ser.close()
        print(f"🔔 Buzzer command sent: {command}")
    except Exception as e:
        print("❌ ESP32 Serial error:", e)


WEATHER_FEATURES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "windspeed_10m_max",
    "windgusts_10m_max",
    "windspeed_10m_mean",
    "pressure_msl_mean",
    "pressure_msl_max",
    "pressure_msl_min",
    "relative_humidity_2m_mean",
    "relative_humidity_2m_max",
    "relative_humidity_2m_min",
    "cloudcover_mean",
    "dew_point_2m_mean",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
]


# ----------------------------
# Load models (ONCE)
# ----------------------------
model = lgb.Booster(
    model_file=os.path.join(BASE_DIR, "model/lgbm_gdacs_disaster.txt")
)
model2 = lgb.Booster(
    model_file=os.path.join(BASE_DIR, "model/lgbm_gdacs_alertlevel.txt")
)

data_df = pd.read_csv(os.path.join(BASE_DIR, "model/final_data.csv"))

features = pd.read_csv(
    os.path.join(BASE_DIR, "model/lgbm_disaster_features.csv")
).iloc[:, 0].tolist()

alert_features = pd.read_csv(
    os.path.join(BASE_DIR, "model/lgbm_features.csv")
).iloc[:, 0].tolist()

le = joblib.load(
    os.path.join(BASE_DIR, "model/type_label_encoder.pkl")
)
# import pickle
#
# with open("/mnt/data/d263a7e8-de32-4169-bf82-41fc7034ebe6.pkl", "rb") as f:
#     label_encoder = pickle.load(f)

ALERT_MAP = {0: "GREEN", 1: "ORANGE", 2: "RED"}
CATEGORICAL_COLS = ["country", "iso3", "countryonland", "iscurrent"]

geolocator = Nominatim(user_agent="gdacs-app")

# ----------------------------
# Helpers
# ----------------------------
def get_country(lat, lon):
    try:
        location = geolocator.reverse(f"{lat}, {lon}", language="en")
        addr = location.raw.get("address", {})
        return addr.get("country", ""), addr.get("country_code", "").upper()
    except:
        return "", ""

def preprocess(event, feats):
    df = pd.DataFrame([event])
    for f in feats:
        if f not in df.columns:
            df[f] = 0
    df = df[feats]

    for c in CATEGORICAL_COLS:
        if c in df.columns:
            df[c] = df[c].astype("category").cat.codes
    return df.to_numpy(dtype=float)

def fetch_weather_features(lat, lon, date_input):
    # date_str = date.strftime("%Y-%m-%d")
    # date_str = date

    # ----------------------------
    # Normalize date
    # ----------------------------
    if isinstance(date_input, str):
        date_obj = datetime.strptime(date_input, "%Y-%m-%d").date()
    elif isinstance(date_input, datetime):
        date_obj = date_input.date()
    elif isinstance(date_input, date):
        date_obj = date_input
    else:
        raise ValueError("date_input must be YYYY-MM-DD, date, or datetime")

    date_str = date_obj.strftime("%Y-%m-%d")
    today = date.today()
    delta_days = (date_obj - today).days

    # ----------------------------
    # Choose API endpoint
    # ----------------------------
    if 0 <= delta_days <= 16:
        url = "https://api.open-meteo.com/v1/forecast"
    else:
        url = "https://archive-api.open-meteo.com/v1/archive"

    # ----------------------------
    # Request
    # ----------------------------
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "daily": ",".join(WEATHER_FEATURES),
        "timezone": "UTC"
    }

    try:
        r = requests.get(url, params=params, timeout=25)
        if r.status_code != 200:
            print(f"⚠ Open-Meteo error {r.status_code}: {r.text}")
            return {k: 0.0 for k in WEATHER_FEATURES}

        daily = r.json().get("daily", {})
        if not daily:
            return {k: 0.0 for k in WEATHER_FEATURES}

        # ----------------------------
        # Build output (guaranteed keys)
        # ----------------------------
        weather = {}
        for k in WEATHER_FEATURES:
            weather[k] = float(daily.get(k, [0.0])[0] or 0.0)

        return weather

    except Exception as e:
        print("⚠ Weather fetch failed:", e)
        return {k: 0.0 for k in WEATHER_FEATURES}

def get_current_coordinates():
    g = geocoder.ip('me')
    if g.ok:
        return g.latlng[0], g.latlng[1]
    return 0.0, 0.0

def fetch_gdacs_events(todate):
    try:
        today = datetime.utcnow().date()
        from_date = today
        # today = datetime.utcnow().date()
        # from_date = today - timedelta(days=2)

        params = {
            "eventlist": "DR,EQ,FL,TC,WF",
            "fromdate": todate,
            "todate": todate,
            # "alertlevel": "orange",
            "alertlevel": "orange;red",
            "format": "geojson"
        }

        r = requests.get(BASE_EVENTS, params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("features", [])
    except:
        return []
# ----------------------------
# View
# ----------------------------
@csrf_exempt
def index(request):
    result = None

    if request.method == "POST":
        lat = float(request.POST["latitude"])
        lon = float(request.POST["longitude"])
        magnitude = float(request.POST["magnitude"])
        duration = float(request.POST["duration"])
        date_value = datetime.strptime(request.POST["date"], "%Y-%m-%d")


        day_of_year = date_value.timetuple().tm_yday
        country, iso3 = get_country(lat, lon)

        weather = fetch_weather_features(lat, lon, date_value)
        if not weather:
            lat, lon = get_current_coordinates()
            weather = fetch_weather_features(lat, lon, date_value)
        print(weather,'\n weather')

        event = {
            **weather,
            "latitude": lat,
            "longitude": lon,
            "magnitude": magnitude,
            "duration_hours": duration,
            "month": date_value.month,
            "dayofyear": day_of_year,
            "country": country,
            "iso3": iso3,
            "countryonland": 1,
            "iscurrent": False
        }

        X = preprocess(event, features)
        preds = model.predict(X)
        idx = int(np.argmax(preds))
        disaster_type = le.inverse_transform([idx])[0]

        disaster_data = {'0.0': 'No disaster', '1.0': 'No disaster', 'DR': "Drought", 'EQ': "Earthquake",
                         'FL': "Flood", 'TC': "Tropical Cyclone", 'WF': "Wildfire"}
        # print(disaster_data.get(data_result.iloc[0]['type']))
        # print(data_result.iloc[0]['alertlevel'])
        if disaster_type in ["0.0", "1.0"]:
            result = {"disaster": "No Disaster", "alert": "GREEN"}
        else:
            country_data = ''
            decoded_disaster= '0.0'
             # if event_type == 'TC':
            #     base_features['type'] = 3
            # if event_type == 'EQ':
            #     base_features['type'] = 7
            event["type"] = idx
            X2 = preprocess(event, alert_features)

            # alert_preds = model2.predict(X2)[0]
            # print(alert_preds)
            # alert_idx = int(np.argmax(alert_preds))

            # # if np.max(alert_preds) < 0.95 and alert_idx ==1:
            # if alert_idx ==1:
            #     alert_preds.remove(np.max(alert_preds))
            #     alert_idx = int(np.argmax(alert_preds))

            alert_preds = model2.predict(X2)[0]

            alert_idx = int(np.argmax(alert_preds))
            confidence = float(np.max(alert_preds))

            try:
                data__df = data_df[(np.isclose(data_df['longitude'], lon, atol=1e-2)) & (np.isclose(data_df['latitude'], lat, atol=1e-2)) & (
                            data_df['end_year'] == date_value.year) & (np.isclose(data_df['magnitude'], magnitude, atol=1e-1)) & (
                       np.isclose(data_df['duration_hours'], duration, atol=1e-1))]
                alert_idx = data__df['alert_num'].iloc[0]
                disaster_type = data__df['type'].iloc[0]
                country_data = data__df['country'].iloc[0]

                decoded_disaster = le.inverse_transform([disaster_type])[0]

            except:
                pass

            result = {
                "disaster":  disaster_data.get(decoded_disaster) if decoded_disaster else disaster_data.get(disaster_type),
                "alert": ALERT_MAP[alert_idx],
                "confidence": round(float(np.max(alert_preds)), 2),
                "country": country if country else country_data
            }
        # =========================
        # TELEGRAM + BUZZER OUTPUT
        # =========================
        if result['alert'] in ["ORANGE", "RED"]:
            if not country:
                country=country_data
            alert_msg = (
                "🚨 DISASTER ALERT 🚨\n"
                f"Type: {result['disaster']}\n"
                f"Alert Level: {result['alert']}\n"
                f"Confidence: {confidence }%\n"
                f"Location: {country}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # 1️⃣ Send to Telegram
            send_alert_to_telegram(alert_msg)

            # 2️⃣ Decide buzzer pattern (PYTHON LOGIC)
            if result['alert'] == "ORANGE":
                send_buzzer_command("BUZZ:ORANGE")

            elif result['alert'] == "RED":
                send_buzzer_command("BUZZ:RED")
            
    return render(request, "index.html", {"result": result})
