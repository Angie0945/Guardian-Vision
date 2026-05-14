import streamlit as st
import paho.mqtt.client as paho
import json
import numpy as np
from PIL import Image
from ultralytics import YOLO
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import random

# =========================================================
# CONFIGURACIÓN
# =========================================================
st.set_page_config(
    page_title="Guardian Vision Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ESTILOS VISUALES
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
    background-color: #f2f2f2 !important;
    border-right: 3px solid #1d4ed8;
}

/* Header */
.main-header {
    background: linear-gradient(90deg, #111827, #2563eb);
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    color: white !important;
    margin-bottom: 20px;
}

/* Tarjetas */
.card {
    background: white;
    padding: 20px;
    border-radius: 18px;
    border: 2px solid #2563eb;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* Botones Streamlit */
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

/* Bokeh botón */
div.bk-root {
    display: flex !important;
    justify-content: center !important;
    margin-top: 15px !important;
}

/* Estados */
.estado-on {
    padding: 15px;
    background-color: #fee2e2;
    color: #b91c1c;
    border-radius: 12px;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
}

.estado-off {
    padding: 15px;
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
    <h1>🛡️ GUARDIAN VISION PRO</h1>
    <h3>Seguridad Inteligente | Voz + IA + MQTT</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("📘 Instrucciones")
    st.write("### 🎙️ Voz")
    st.write("Presiona ESCUCHAR y di:")
    st.write("- enciende la alarma")
    st.write("- apaga la alarma")

    st.write("### 🔘 Manual")
    st.write("- Botón de encendido")
    st.write("- Botón de apagado")

    st.write("### 📸 Vigilancia")
    st.write("La cámara analiza cada imagen capturada.")
    st.write("Si detecta una persona con la alarma activa, genera alerta.")

# =========================================================
# MQTT
# =========================================================
broker = "broker.mqttdashboard.com"
port = 1883

@st.cache_resource
def setup_mqtt():
    client = paho.Client(paho.CallbackAPIVersion.VERSION1, "ANGIE_GUARDIAN")
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
# ESTADO
# =========================================================
if "alarma_activa" not in st.session_state:
    st.session_state.alarma_activa = False

frases_alerta = [
    "🚨 Intruso detectado",
    "⚠️ Persona no autorizada",
    "🔴 Movimiento sospechoso",
    "🚨 Alarma activada por presencia humana"
]

# =========================================================
# COLUMNAS
# =========================================================
col1, col2 = st.columns([1, 2])

# =========================================================
# PANEL IZQUIERDO
# =========================================================
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("🎙️ Control por Voz")

    stt_button = Button(label="🎙️ ESCUCHAR", width=250, height=70, button_type="success")

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
# PANEL DERECHO - CÁMARA
# =========================================================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("📸 Vigilancia Inteligente")

    st.info("La cámara analiza cada captura. Para monitoreo continuo, sigue tomando imágenes.")

    img_buffer = st.camera_input("Captura de vigilancia")

    if img_buffer:
        img = Image.open(img_buffer).convert("RGB")
        frame = np.array(img)

        results = model(frame, conf=0.45)

        detecciones = [model.names[int(box.cls)] for box in results[0].boxes]

        if "person" in detecciones and st.session_state.alarma_activa:
            alerta = random.choice(frases_alerta)

            st.error(alerta)

            mqtt_client.publish("voice_ctrl", json.dumps({
                "Act1": "INTRUSO"
            }))

            st.image(
                results[0].plot()[:, :, ::-1],
                caption="🚨 Intruso Detectado",
                use_container_width=True
            )

        else:
            st.image(
                frame,
                caption="🛡️ Área Segura",
                use_container_width=True
            )

            if st.session_state.alarma_activa:
                st.success("Sistema activo sin amenazas.")
            else:
                st.warning("Sistema apagado.")

    st.markdown('</div>', unsafe_allow_html=True)
