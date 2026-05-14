import streamlit as st
from PIL import Image
import io
import numpy as np
from ultralytics import YOLO
import paho.mqtt.client as paho
import json
import random
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# =========================================================
# 1. CONFIGURACIÓN Y ESTILOS (Angie Style: Contraste Alto)
# =========================================================
st.set_page_config(page_title="Guardian Vision Pro", layout="wide")

st.markdown("""
<style>
    /* Fondo con degradado suave */
    .stApp {
        background: linear-gradient(135deg, #f3e8ff, #e5d9ff);
        color: #1f1f1f;
    }
    
    /* Contenedor del Título (Alto Contraste) */
    .header-container {
        background: linear-gradient(90deg, #2d1457 0%, #6a0dad 100%);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        color: #ffffff; /* Blanco puro para contraste */
        margin-bottom: 10px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
    }

    /* Tarjetas de Interfaz */
    .project-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 15px;
        border: 2px solid #2d1457;
        text-align: center;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    }

    /* Eliminar espacios blancos de Streamlit */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* Estilo para el botón de voz */
    .bk-btn-default {
        background-color: #6a0dad !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }
</style>

<div class="header-container">
    <h1 style='margin:0;'>🛡️ GUARDIAN VISION PRO</h1>
    <p style='margin:0; font-weight:bold; opacity:0.9;'>Seguridad Inteligente: Visión Artificial + Voz</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 2. MQTT & MODELOS (Paho v2.0 compatible)
# =========================================================
broker = "broker.mqttdashboard.com"
port = 1883

@st.cache_resource
def get_mqtt_client():
    # Usamos la versión de API 1 para mantener compatibilidad con tu lógica
    client = paho.Client(paho.CallbackAPIVersion.VERSION1, "GUARDIAN_ANGIE")
    client.connect(broker, port)
    return client

mqtt_c = get_mqtt_client()

@st.cache_resource
def load_yolo():
    return YOLO("yolov8n.pt")

yolo_model = load_yolo()

if 'alarma_activa' not in st.session_state:
    st.session_state.alarma_activa = False

# =========================================================
# 3. INTERFAZ DE CONTROL (VOZ Y ESTADO)
# =========================================================
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="project-card">', unsafe_allow_html=True)
    st.subheader("🎙️ Control por Voz")
    
    # Botón Bokeh para grabar voz
    stt_button = Button(label="🎙️ ESCUCHAR COMANDO", width=250, height=50)
    stt_button.js_on_event("button_click", CustomJS(code="""
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        var recognition = new SpeechRecognition();
        recognition.lang = 'es-ES';
        recognition.onresult = function(e) {
            var value = e.results[0][0].transcript;
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        };
        recognition.start();
    """))

    result = streamlit_bokeh_events(stt_button, events="GET_TEXT", key="listen", override_height=70)

    if result and "GET_TEXT" in result:
        comando = result.get("GET_TEXT").strip().lower()
        st.info(f"Escuché: **{comando}**")
        
        # Lógica de frases específicas
        if "enciende" in comando or "activar" in comando or "enciende la alarma" in comando:
            st.session_state.alarma_activa = True
            mqtt_c.publish("voice_ctrl", json.dumps({"Act1": "activado"}))
            st.success("✅ Alarma Encendida")
        elif "apaga" in comando or "desactivar" in comando or "apaga la alarma" in comando:
            st.session_state.alarma_activa = False
            mqtt_c.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))
            st.warning("⚠️ Alarma Apagada")
    
    st.markdown("---")
    # Indicador visual de estado
    if st.session_state.alarma_activa:
        st.markdown("<h3 style='color:red;'>🔴 SISTEMA: VIGILANDO</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='color:green;'>🟢 SISTEMA: OFF</h3>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 4. VIGILANCIA (VISIÓN ARTIFICIAL)
# =========================================================
with col2:
    st.markdown('<div class="project-card">', unsafe_allow_html=True)
    img_file_buffer = st.camera_input("📸 Cámara de Vigilancia")

    if img_file_buffer and st.session_state.alarma_activa:
        img = Image.open(img_file_buffer).convert("RGB")
        results = yolo_model(np.array(img), conf=0.4)
        
        # Detección de personas
        clases_detectadas = [yolo_model.names[int(box.cls)] for box in results[0].boxes]
        
        if "person" in clases_detectadas:
            st.error("🚨 ¡MOVIMIENTO DETECTADO! ENVIANDO ALERTA...")
            mqtt_c.publish("voice_ctrl", json.dumps({"Act1": "INTRUSO"}))
            
            # Banco de frases (Salida de Audio textual)
            frases = ["Se detecta alguien en la imagen", "Movimiento detectado", "Alerta de intruso"]
            st.subheader(f"🗣️ {random.choice(frases)}")
            
            # Mostrar imagen anotada
            st.image(results[0].plot()[:, :, ::-1], use_container_width=True)
        else:
            st.image(img, use_container_width=True)
            st.write("🔍 Escaneando... No hay nadie.")
    elif not st.session_state.alarma_activa:
        st.write("😴 El sistema está durmiendo. Actívalo por voz.")
    st.markdown('</div>', unsafe_allow_html=True)
