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
# 1. CONFIGURACIÓN Y ESTILOS (Angie Style)
# =========================================================
st.set_page_config(page_title="Guardian Vision Pro", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #d9c2ff, #f3e8ff); color: #1f1f1f; }
    .header-container {
        background: linear-gradient(90deg, #6a0dad, #9b59b6);
        padding: 30px; border-radius: 15px; text-align: center; color: white;
        margin-bottom: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    }
    .project-card {
        background-color: white; padding: 20px; border-radius: 15px;
        border: 2px solid #6a0dad; text-align: center; height: 100%;
    }
</style>
<div class="header-container">
    <h1>🛡️ GUARDIAN VISION: SEGURIDAD INTELIGENTE</h1>
    <p>Detección YOLO + Control por Voz MQTT</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 2. MQTT & MODELOS
# =========================================================
broker = "broker.mqttdashboard.com" # El que usas en tus códigos
port = 1883
from paho.mqtt import client as paho # Asegúrate de tener el import así

client1 = paho.Client(paho.CallbackAPIVersion.VERSION1, "GUARDIAN_PRO")

@st.cache_resource
def load_yolo():
    return YOLO("yolov8n.pt") # YOLOv8 Nano para velocidad

yolo_model = load_yolo()

if 'alarma_activa' not in st.session_state:
    st.session_state.alarma_activa = False

# =========================================================
# 3. INTERFAZ DE CONTROL (VOZ Y ESTADO)
# =========================================================
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="project-card">', unsafe_allow_html=True)
    st.subheader("🎤 Control por Voz")
    
    # Botón Bokeh de tu código original
    stt_button = Button(label="🎧 ESCUCHAR COMANDO", width=200, height=60)
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

    result = streamlit_bokeh_events(stt_button, events="GET_TEXT", key="listen", override_height=80)

    if result and "GET_TEXT" in result:
        comando = result.get("GET_TEXT").strip().lower()
        st.write(f"Último comando: *{comando}*")
        
        if "enciende" in comando or "activar" in comando:
            st.session_state.alarma_activa = True
            client1.connect(broker, port)
            client1.publish("voice_ctrl", json.dumps({"Act1": "activado"}))
        elif "apaga" in comando or "desactivar" in comando:
            st.session_state.alarma_activa = False
            client1.connect(broker, port)
            client1.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))
    
    st.markdown("---")
    if st.session_state.alarma_activa:
        st.error("🛡️ SISTEMA: VIGILANDO")
    else:
        st.success("🔓 SISTEMA: DESARMADO")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 4. VIGILANCIA (VISIÓN ARTIFICIAL)
# =========================================================
with col2:
    img_file_buffer = st.camera_input("📸 Cámara de Vigilancia")

    if img_file_buffer and st.session_state.alarma_activa:
        img = Image.open(img_file_buffer).convert("RGB")
        results = yolo_model(np.array(img), conf=0.4)
        
        # Lógica de detección de personas
        clases_detectadas = [yolo_model.names[int(box.cls)] for box in results[0].boxes]
        
        if "person" in clases_detectadas:
            st.markdown('<div style="background-color:#ff4b4b; color:white; padding:15px; border-radius:10px; text-align:center;">', unsafe_allow_html=True)
            st.write("⚠️ ¡INTRUSO DETECTADO! ACTIVANDO ALARMA FÍSICA")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Enviar Alerta a Wokwi
            client1.connect(broker, port)
            client1.publish("voice_ctrl", json.dumps({"Act1": "INTRUSO"}))
            
            # Banco de frases (Salida de Audio)
            frases = ["Se detecta alguien en la imagen", "Movimiento sospechoso detectado", "Alerta de seguridad activada"]
            st.info(f"🗣️ Audio: {random.choice(frases)}")
            
            # Mostrar imagen con detecciones
            st.image(results[0].plot()[:, :, ::-1], use_container_width=True)
        else:
            st.image(img, use_container_width=True)
            st.caption("✅ Área despejada...")
