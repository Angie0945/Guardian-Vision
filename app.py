import streamlit as st
import cv2
import numpy as np
from paho.mqtt import client as mqtt_client
import time

# --- CONFIGURACIÓN MQTT ---
BROKER = 'broker.hivemq.com'
PORT = 1883
TOPIC = "guardian/vision/alarma"
CLIENT_ID = f'python-mqtt-{np.random.randint(0, 1000)}'

def connect_mqtt():
    client = mqtt_client.Client(CLIENT_ID)
    client.connect(BROKER, PORT)
    return client

client = connect_mqtt()

# --- INTERFAZ (Tu estética de tarjetas) ---
st.set_page_config(page_title="Guardian Vision", layout="wide")

st.markdown("""
    <style>
    .header-container {
        background: linear-gradient(90deg, #6f42c1 0%, #e83e8c 100%);
        padding: 40px; border-radius: 15px; text-align: center;
    }
    </style>
    <div class="header-container">
        <h1 style='color: white;'>Mis Aplicaciones de IA: Guardian Vision</h1>
    </div>
    """, unsafe_allow_html=True)

# Lógica de Control
col1, col2 = st.columns(2)
with col1:
    activar = st.button("🚨 ACTIVAR SEGURIDAD")
    if activar:
        st.session_state['seguridad'] = True
        client.publish(TOPIC, "SISTEMA_ON")

with col2:
    desactivar = st.button("🟢 DESACTIVAR")
    if desactivar:
        st.session_state['seguridad'] = False
        client.publish(TOPIC, "SISTEMA_OFF")

# --- VISIÓN ARTIFICIAL (Detección de Movimiento) ---
img_file_buffer = st.camera_input("Monitoreo en Tiempo Real")

if img_file_buffer is not None and st.session_state.get('seguridad'):
    # Aquí iría la lógica de comparación de frames de OpenCV
    # Si detecta movimiento:
    client.publish(TOPIC, "INTRUSO")
    st.error("⚠️ ¡MOVIMIENTO DETECTADO!")
