import streamlit as st
import paho.mqtt.client as paho
import json
import numpy as np
import av
from ultralytics import YOLO
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import random

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Guardian Vision ULTRA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ESTILOS PREMIUM
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: white;
    color: black;
}

html, body, [class*="css"] {
    color: black !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #f3f4f6 !important;
    border-right: 4px solid #111827;
}

/* Header */
.main-header {
    background: linear-gradient(90deg, #111827, #2563eb);
    padding: 28px;
    border-radius: 20px;
    text-align: center;
    color: white !important;
    margin-bottom: 20px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

/* Tarjetas */
.card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    border: 2px solid #d1d5db;
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* Botones */
.stButton>button {
    width: 100%;
    background-color: #2563eb;
    color: white;
    font-size: 18px;
    font-weight: bold;
    border-radius: 12px;
    padding: 12px;
    border: none;
}

.stButton>button:hover {
    background-color: #111827;
    color: white;
}

/* Bokeh */
div.bk-root {
    display: flex !important;
    justify-content: center !important;
    margin-top: 10px !important;
}

/* Estado */
.estado-on {
    padding: 16px;
    background-color: #fee2e2;
    color: #991b1b;
    border-radius: 12px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
}

.estado-off {
    padding: 16px;
    background-color: #dcfce7;
    color: #166534;
    border-radius: 12px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="main-header">
    <h1>🛡️ GUARDIAN VISION ULTRA</h1>
    <h3>Seguridad Inteligente en Vivo | Voz + IA + MQTT</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("📘 Panel de Instrucciones")
    st.write("### 🎙️ Comandos de Voz")
    st.write("- enciende la alarma")
    st.write("- apaga la alarma")

    st.write("### 🔘 Control Manual")
    st.write("- Botón de encendido")
    st.write("- Botón de apagado")

    st.write("### 🎥 Monitoreo")
    st.write("La cámara analiza en vivo.")
    st.write("Solo alerta si la alarma está activa.")

    st.write("### 🚨 Detección")
    st.write("Detecta personas automáticamente.")

# =========================================================
# MQTT
# =========================================================
broker = "broker.mqttdashboard.com"
port = 1883

@st.cache_resource
def setup_mqtt():
    client = paho.Client(paho.CallbackAPIVersion.VERSION1, "ANGIE_ULTRA")
    client.connect(broker, port)
    return client

mqtt_client = setup_mqtt()

# =========================================================
# YOLO
# =========================================================
@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")

model = load_model()

# =========================================================
# SESSION
# =========================================================
if "alarma_activa" not in st.session_state:
    st.session_state.alarma_activa = False

frases_alerta = [
    "🚨 INTRUSO DETECTADO",
    "⚠️ PERSONA NO AUTORIZADA",
    "🔴 MOVIMIENTO SOSPECHOSO",
    "🚨 ALERTA DE SEGURIDAD"
]

# =========================================================
# VIDEO PROCESSOR
# =========================================================
class VideoProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        if st.session_state.alarma_activa:
            results = model(img, conf=0.45)

            detecciones = [model.names[int(box.cls)] for box in results[0].boxes]

            if "person" in detecciones:
                mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "INTRUSO"}))

            annotated = results[0].plot()
            return av.VideoFrame.from_ndarray(annotated, format="bgr24")

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# =========================================================
# LAYOUT
# =========================================================
col1, col2 = st.columns([1, 2])

# =========================================================
# PANEL CONTROL
# =========================================================
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("🎙️ Control por Voz")

    stt_button = Button(label="🎙️ ESCUCHAR", width=240, height=70, button_type="success")

    stt_button.js_on_event("button_click", CustomJS(code="""
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        var recognition = new SpeechRecognition();
        recognition.lang = 'es-ES';
        recognition.continuous = false;
        recognition.interimResults = false;

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
        override_height=90,
        debounce_time=0
    )

    if result and "GET_TEXT" in result:
        comando = result.get("GET_TEXT").lower().strip()

        st.success(f"🗣️ Comando: {comando}")

        if "enciende la alarma" in comando:
            st.session_state.alarma_activa = True
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))

        elif "apaga la alarma" in comando:
            st.session_state.alarma_activa = False
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))

    st.write("### 🔘 Control Manual")

    if st.button("🟢 ENCENDER ALARMA"):
        st.session_state.alarma_activa = True
        mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))

    if st.button("🔴 APAGAR ALARMA"):
        st.session_state.alarma_activa = False
        mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))

    if st.session_state.alarma_activa:
        st.markdown('<div class="estado-on">🔴 ALARMA ACTIVADA</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="estado-off">🟢 ALARMA APAGADA</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# PANEL VIDEO EN VIVO
# =========================================================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("🎥 Vigilancia en Tiempo Real")

    rtc_configuration = RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )

    webrtc_streamer(
        key="guardian-vision",
        video_processor_factory=VideoProcessor,
        rtc_configuration=rtc_configuration,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    if st.session_state.alarma_activa:
        st.error(random.choice(frases_alerta))
    else:
        st.success("Sistema en espera.")

    st.markdown('</div>', unsafe_allow_html=True)
