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
# 1. CONFIGURACIÓN Y ESTILOS (Alto Contraste y Cero Espacios)
# =========================================================
st.set_page_config(page_title="Guardian Vision Pro", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f4f1fa; color: #1f1f1f; }
    
    /* Encabezado con alto contraste */
    .header-container {
        background: linear-gradient(90deg, #2d1457 0%, #6a0dad 100%);
        padding: 20px; border-radius: 15px; text-align: center;
        color: #FFFFFF; margin-bottom: 10px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }

    /* Tarjetas compactas */
    .project-card {
        background-color: #ffffff; padding: 15px; border-radius: 15px;
        border: 2px solid #2d1457; text-align: center;
    }

    /* Eliminar espacios blancos innecesarios */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    div[data-testid="stVerticalBlock"] > div { margin-top: -0.5rem !important; }
</style>

<div class="header-container">
    <h1 style='margin:0; font-size: 32px;'>🛡️ GUARDIAN VISION PRO</h1>
    <p style='margin:0; font-weight:bold; color: #E0E0E0;'>Seguridad Multimodal: Visión + Voz</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 2. MQTT Y MODELO (Compatibilidad Paho v2)
# =========================================================
broker = "broker.mqttdashboard.com"
port = 1883

@st.cache_resource
def get_mqtt_client():
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
# 3. INTERFAZ: CONTROL POR VOZ (Lado Izquierdo)
# =========================================================
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="project-card">', unsafe_allow_html=True)
    st.subheader("🎤 Control por Voz")
    
    # Botón Bokeh para grabar voz
    stt_button = Button(label="🎙️ ESCUCHAR COMANDO", width=260, height=70, button_type="primary")
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
        st.write(f"Comando detectado: **{comando}**")
        
        if "enciende la alarma" in comando or "activar" in comando:
            st.session_state.alarma_activa = True
            mqtt_c.publish("voice_ctrl", json.dumps({"Act1": "activado"}))
            st.success("✅ Alarma Encendida")
        elif "apaga la alarma" in comando or "desactivar" in comando:
            st.session_state.alarma_activa = False
            mqtt_c.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))
            st.warning("⚠️ Alarma Apagada")
    
    st.markdown("---")
    if st.session_state.alarma_activa:
        st.markdown("<h2 style='color:#d9534f; margin:0;'>🔴 VIGILANDO</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='color:#5cb85c; margin:0;'>🟢 STANDBY</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 4. VIGILANCIA: VISIÓN ARTIFICIAL (Lado Derecho)
# =========================================================
with col2:
    st.markdown('<div class="project-card">', unsafe_allow_html=True)
    img_file_buffer = st.camera_input("📸 Cámara de Seguridad")

    if img_file_buffer and st.session_state.alarma_activa:
        img = Image.open(img_file_buffer).convert("RGB")
        results = yolo_model(np.array(img), conf=0.4)
        
        # Detección de personas
        clases_detectadas = [yolo_model.names[int(box.cls)] for box in results[0].boxes]
        
        if "person" in clases_detectadas:
            st.error("🚨 ¡INTRUSO DETECTADO!")
            mqtt_c.publish("voice_ctrl", json.dumps({"Act1": "INTRUSO"}))
            
            # Banco de frases para el feedback visual
            frases = ["¡Alerta! Alguien entró en la zona.", "Movimiento detectado.", "Seguridad activada."]
            st.info(f"🗣️ {random.choice(frases)}")
            
            # Imagen con cuadros de detección
            st.image(results[0].plot()[:, :, ::-1], use_container_width=True)
        else:
            st.image(img, use_container_width=True)
            st.write("✅ Todo en orden...")
    elif not st.session_state.alarma_activa:
        st.info("😴 Sistema en reposo. Di 'Enciende la alarma' para comenzar.")
    st.markdown('</div>', unsafe_allow_html=True)
