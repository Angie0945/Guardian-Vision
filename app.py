# =========================================================
# GUARDIAN VISION PRO - VIGILANCIA EN TIEMPO REAL
# Angie Version FINAL - Monitoreo continuo + Voz + MQTT + Contraste
# =========================================================

import streamlit as st
import paho.mqtt.client as paho
import json
import numpy as np
from PIL import Image
from ultralytics import YOLO
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from streamlit_autorefresh import st_autorefresh
import time
import random

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Guardian Vision Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Refresco automático cada 3 segundos para vigilancia continua
st_autorefresh(interval=3000, key="guardian_refresh")

# =========================================================
# ESTILOS - FONDO BLANCO + TEXTO NEGRO + ALTO CONTRASTE
# =========================================================
st.markdown("""
<style>
/* Fondo general */
.stApp {
    background-color: white;
    color: black;
}

/* Todo el texto negro */
html, body, [class*="css"] {
    color: black !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #f4f4f4 !important;
    border-right: 3px solid #1f4e79;
}

/* Encabezado */
.main-header {
    background: linear-gradient(90deg, #0f172a, #1d4ed8);
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    color: white !important;
    margin-bottom: 20px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
}

/* Tarjetas */
.card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 18px;
    border: 3px solid #1d4ed8;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

/* Botones grandes */
.stButton>button {
    width: 100%;
    background-color: #1d4ed8;
    color: white;
    font-size: 18px;
    font-weight: bold;
    border-radius: 12px;
    padding: 12px;
    border: none;
}

.stButton>button:hover {
    background-color: #0f172a;
    color: white;
}

/* Bokeh botón */
div.bk-root {
    display: flex !important;
    justify-content: center !important;
    margin-top: 15px !important;
}

/* Alertas */
.alert-box {
    padding: 15px;
    border-radius: 12px;
    font-weight: bold;
    text-align: center;
    font-size: 22px;
}

/* Estado ON */
.on-state {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 2px solid red;
}

/* Estado OFF */
.off-state {
    background-color: #dcfce7;
    color: #166534;
    border: 2px solid green;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="main-header">
    <h1>🛡️ GUARDIAN VISION PRO</h1>
    <h3>Vigilancia Inteligente en Tiempo Real | Voz + IA + MQTT</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR - INSTRUCCIONES
# =========================================================
with st.sidebar:
    st.title("📘 Instrucciones")
    st.markdown("""
### 🎙️ Control por Voz:
**Presiona ESCUCHAR y di:**
- **“enciende la alarma”**
- **“apaga la alarma”**

### 📸 Vigilancia:
- La cámara monitorea constantemente.
- Solo genera alerta si la alarma está ACTIVADA.
- Detecta personas automáticamente.

### 🚨 Respuesta:
- MQTT envía señal al hardware
- Alerta visual
- Mensaje de intruso

### 🛡️ Recomendación:
Mantén la cámara apuntando al área de vigilancia.
""")

# =========================================================
# MQTT
# =========================================================
broker = "broker.mqttdashboard.com"
port = 1883

@st.cache_resource
def setup_mqtt():
    client = paho.Client(paho.CallbackAPIVersion.VERSION1, "ANGIE_GUARDIAN_PRO")
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
# ESTADOS
# =========================================================
if "alarma_activa" not in st.session_state:
    st.session_state.alarma_activa = False

if "ultima_alerta" not in st.session_state:
    st.session_state.ultima_alerta = ""

# Frases de alerta
frases_intruso = [
    "🚨 Atención: Intruso detectado.",
    "⚠️ Alerta máxima: Persona no autorizada.",
    "🔴 Movimiento sospechoso detectado.",
    "🚨 Seguridad activada: Presencia humana encontrada."
]

# =========================================================
# LAYOUT PRINCIPAL
# =========================================================
col1, col2 = st.columns([1, 2])

# =========================================================
# PANEL DE CONTROL
# =========================================================
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎙️ Panel de Voz")

    # BOTÓN DE ESCUCHA REAL
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

    # Procesar voz
    if result and "GET_TEXT" in result:
        comando = result.get("GET_TEXT").lower().strip()
        st.success(f"🗣️ Comando detectado: {comando}")

        if "enciende la alarma" in comando:
            st.session_state.alarma_activa = True
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))

        elif "apaga la alarma" in comando:
            st.session_state.alarma_activa = False
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))

    # Botones manuales
    st.write("### 🔘 Control Manual")

    if st.button("🟢 ENCENDER ALARMA"):
        st.session_state.alarma_activa = True
        mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))

    if st.button("🔴 APAGAR ALARMA"):
        st.session_state.alarma_activa = False
        mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))

    # Estado visual
    if st.session_state.alarma_activa:
        st.markdown('<div class="alert-box on-state">🔴 ALARMA ACTIVADA</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box off-state">🟢 ALARMA DESACTIVADA</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# CÁMARA DE VIGILANCIA CONTINUA
# =========================================================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📸 Cámara de Vigilancia en Tiempo Real")

    img_buffer = st.camera_input("")

    if img_buffer is not None:
        img = Image.open(img_buffer).convert("RGB")
        frame = np.array(img)

        # Detección continua
        results = model(frame, conf=0.45)

        detecciones = [model.names[int(box.cls)] for box in results[0].boxes]

        # Si hay persona y alarma activa
        if "person" in detecciones and st.session_state.alarma_activa:
            alerta = random.choice(frases_intruso)

            st.error(alerta)

            mqtt_client.publish("voice_ctrl", json.dumps({
                "Act1": "INTRUSO"
            }))

            st.image(results[0].plot()[:, :, ::-1], caption="🚨 Intruso Detectado", use_container_width=True)

        else:
            st.image(frame, caption="🛡️ Monitoreo Activo", use_container_width=True)

            if st.session_state.alarma_activa:
                st.success("Área segura")
            else:
                st.info("Sistema en espera. Activa la alarma para protección.")

    else:
        st.warning("Activa la cámara para iniciar vigilancia.")

    st.markdown('</div>', unsafe_allow_html=True)
