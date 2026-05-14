import streamlit as st
import paho.mqtt.client as paho
import json
import numpy as np
from PIL import Image
from ultralytics import YOLO
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# =========================================================
# 1. ESTILOS Y CONFIGURACIÓN (Angie Style)
# =========================================================
st.set_page_config(page_title="Guardian Vision Pro", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #d9c2ff, #f3e8ff); color: #1f1f1f; }
    .header-container {
        background: linear-gradient(90deg, #2d1457 0%, #6a0dad 100%);
        padding: 20px; border-radius: 15px; text-align: center; color: white;
        margin-bottom: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
    }
    .project-card {
        background-color: #ffffffcc; padding: 20px; border-radius: 20px;
        border: 3px solid #6a0dad; text-align: center;
    }
    /* Eliminar espacios blancos del componente Bokeh */
    iframe { background: transparent !important; }
</style>
<div class="header-container">
    <h1 style='margin:0;'>🛡️ GUARDIAN VISION PRO</h1>
    <p style='margin:0;'>Control por Voz MQTT + Inteligencia Artificial</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 2. MODELOS Y MQTT
# =========================================================
broker = "broker.mqttdashboard.com"
port = 1883

@st.cache_resource
def setup_mqtt():
    client = paho.Client(paho.CallbackAPIVersion.VERSION1, "ANGIE_GUARDIAN")
    client.connect(broker, port)
    return client

mqtt_client = setup_mqtt()

@st.cache_resource
def load_yolo():
    return YOLO("yolov8n.pt")

model = load_yolo()

if 'alarma_activa' not in st.session_state:
    st.session_state.alarma_activa = False

# =========================================================
# 3. INTERFAZ: BOTÓN DE VOZ (BOKEH)
# =========================================================
col1, col2 = st.columns([1, 1.5])

with col1:
    st.markdown('<div class="project-card">', unsafe_allow_html=True)
    st.markdown("### 🎙️ Control de Comando")
    
    # Tu botón exacto de Bokeh
    stt_button = Button(label="🎧 ESCUCHAR", width=250, height=60)
    stt_button.js_on_event("button_click", CustomJS(code="""
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        var recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'es-ES';

        recognition.onresult = function(e) {
            var value = e.results[0][0].transcript;
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        };
        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=80,
        debounce_time=0
    )

    if result and "GET_TEXT" in result:
        comando = result.get("GET_TEXT").strip().lower()
        st.info(f"🗣️ Escuché: **{comando}**")
        
        # Lógica de frases solicitadas
        if "enciende la alarma" in comando or "activar" in comando:
            st.session_state.alarma_activa = True
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))
        elif "apaga la alarma" in comando or "desactivar" in comando:
            st.session_state.alarma_activa = False
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))

    st.write("---")
    if st.session_state.alarma_activa:
        st.markdown("<h2 style='color:red;'>🔴 SISTEMA ACTIVO</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='color:green;'>🟢 SISTEMA OFF</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 4. VIGILANCIA: CÁMARA Y YOLO
# =========================================================
with col2:
    img_buffer = st.camera_input("📸 Cámara de Seguridad")

    if img_buffer and st.session_state.alarma_activa:
        img = Image.open(img_buffer).convert("RGB")
        results = model(np.array(img), conf=0.4)
        
        # Buscar personas
        detecciones = [model.names[int(box.cls)] for box in results[0].boxes]
        
        if "person" in detecciones:
            st.error("🚨 ¡INTRUSO DETECTADO!")
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "INTRUSO"}))
            st.image(results[0].plot()[:, :, ::-1], use_container_width=True)
        else:
            st.image(img, use_container_width=True)
            st.success("🔍 Área despejada")
