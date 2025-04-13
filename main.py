import json
import time
import datetime
import paho.mqtt.client as mqtt
import requests

MQTT_BROKER = '192.168.112.204'
MQTT_PORT = 1883
MQTT_TOPIC = 'esp32/sensors'

API_ENDPOINT = 'http://localhost:5173/api/alerts'

# Weights (WIP)
wPIR = 0.1
wUS = 0.1
wAQI = 0.1
wMIC = 0.3
wCAM = 0.4

def calculate_severity(sensor_data):
    IPIR = 1 if sensor_data.get("motion") == 1 else 0
    distance = sensor_data.get("distance_cm", 200)
    IUS = 1 if distance < 1 else 0.5 + ((50 - distance) / 100) if 1 <= distance <= 50 else 0
    aqi = sensor_data.get("aqi", 0)
    IAQI = 0.5 + ((aqi - 1400) / 400) if 1400 <= aqi <= 1600 else 0
    ICAM = sensor_data.get("camera", 0)
    print(f"IPIR: {IPIR}, IUS: {IUS}, IAQI: {IAQI}, ICAM: {ICAM}")
    severity_score = (wPIR * IPIR) + (wUS * IUS) + (wAQI * IAQI) + (wCAM * ICAM)
    return round(severity_score, 2)

def send_alert(score):

    severity = "high" if score >= 0.7 else "medium" if score >= 0.3 else "low"

    alert_data = {
        "nodeId": "QKVumQzAIWsjQiZNyrEA",
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "type": "Intrusion Alert",
        "status": "active",
        "details": f"Severity Score: {score}",
        "severity": "medium" if score >= 0.1 else "low",
        "location": "Sector E-7"
    }
    
    try:
        response = requests.post(API_ENDPOINT, json=alert_data)
        if response.status_code == 200:
            print("Alert sent successfully.")
        else:
            print(f"Failed to send alert. HTTP Status Code: {response.status_code}. Response: {response.text}")
    except requests.RequestException as e:
        print(f"Failed to send alert: {e}")
    

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect to MQTT broker. Code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        sensor_data = json.loads(payload)
        print(f"Received sensor data: {sensor_data}")

        severity = calculate_severity(sensor_data)
        print(f"Severity Score: {severity}")

        if severity >= 0.1:
            send_alert(severity)
        else:
            print("No significant activity detected.")
    except Exception as e:
        print(f"Error processing message: {e}")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")