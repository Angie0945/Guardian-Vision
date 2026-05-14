import streamlit as st
import paho.mqtt.client as paho
import json
import numpy as np
from PIL import Image
from ultralytics import YOLO
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Guardian Vision Pro",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ESTILOS VISUALES (FONDO BLANCO + LETRAS NEGRAS)
# =========================================================
st.markdown("""
<style>
/* Fondo general */
.stApp {
    background-color: white;
    color: black;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #f5f5f5;
    color: black;
}

/* Todo texto negro */
html, body, [class*="css"] {
    color: black !important;
}

/* Header principal */
.main-header {
    background-color: #111111;
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    color: white !important;
    margin-bottom: 20px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
}

/* Tarjetas */
.card {
    background-color: #ffffff;
    border: 2px solid #dcdcdc;
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* Botones Streamlit */
.stButton>button {
    width: 100%;
    border-radius: 12px;
    background-color: black;
    color: white;
    font-size: 18px;
    font-weight: bold;
    padding: 12px;
}

/* Bokeh centrado */
div.bk-root {
    display: flex !important;
    justify-content: center !important;
    margin-top: 10px;
    margin-bottom: 10px;
}

/* Cámara */
[data-testid="stCameraInput"] {
    border: 2px solid #cccccc;
    border-radius: 15px;
    padding: 10px;
}

/* Títulos */
h1, h2, h3 {
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="main-header">
    <h1>🛡️ GUARDIAN VISION PRO</h1>
    <h3>Seguridad Inteligente con Voz + Cámara + MQTT</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR EXPLICATIVA
# =========================================================
with st.sidebar:
    st.title("📘 Instrucciones")
    st.write("""
    ### ¿Cómo usar?
    
    **1️⃣ Activar sistema:**  
    Presiona **🎙️ ESCUCHAR** y di:  
    **"enciende la alarma"**
    
    **2️⃣ Desactivar sistema:**  
    Di:  
    **"apaga la alarma"**
    
    **3️⃣ Vigilancia:**  
    Usa la cámara para detectar personas.
    
    **4️⃣ Resultado:**  
    - Si detecta persona → 🚨 Alarma  
    - Si no → ✅ Seguro
    """)

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
# MODELO YOLO
# =========================================================
@st.cache_resource
def load_yolo():
    return YOLO("yolov8n.pt")

model = load_yolo()

# =========================================================
# ESTADO
# =========================================================
if "alarma_activa" not in st.session_state:
    st.session_state.alarma_activa = False

# =========================================================
# COLUMNAS PRINCIPALES
# =========================================================
col1, col2 = st.columns([1, 1.4])

# =========================================================
# PANEL DE VOZ
# =========================================================
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎤 Control por Voz")
    st.write("Presiona el botón y da una instrucción")

    # Botón de voz real
    stt_button = Button(label="🎙️ ESCUCHAR", width=250, height=70, button_type="primary")

    stt_button.js_on_event("button_click", CustomJS(code="""
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        var recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'es-ES';

        recognition.onresult = function(e) {
            var value = e.results[0][0].transcript;
            document.dispatchEvent(
                new CustomEvent("GET_TEXT", {detail: value})
            );
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
        comando = result["GET_TEXT"].lower().strip()

        st.success(f"🗣️ Comando detectado: {comando}")

        if "enciende la alarma" in comando or "activar" in comando:
            st.session_state.alarma_activa = True
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))
            st.success("✅ Alarma ACTIVADA")

        elif "apaga la alarma" in comando or "desactivar" in comando:
            st.session_state.alarma_activa = False
            mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))
            st.warning("⚠️ Alarma DESACTIVADA")

        else:
            st.info("Comando no reconocido")

    st.markdown("---")

    # Estado visual
    if st.session_state.alarma_activa:
        st.error("🔴 ESTADO: ALARMA ENCENDIDA")
    else:
        st.success("🟢 ESTADO: SISTEMA APAGADO")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# PANEL DE CÁMARA
# =========================================================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📸 Vigilancia Inteligente")

    img_buffer = st.camera_input("Tomar foto de monitoreo")

    if img_buffer:

        img = Image.open(img_buffer).convert("RGB")

        if st.session_state.alarma_activa:

            with st.spinner("Analizando imagen..."):
                results = model(np.array(img), conf=0.4)

            detecciones = [
                model.names[int(box.cls)]
                for box in results[0].boxes
            ]

            if "person" in detecciones:
                st.error("🚨 ¡INTRUSO DETECTADO!")
                mqtt_client.publish(
                    "voice_ctrl",
                    json.dumps({"Act1": "INTRUSO"})
                )

                st.image(
                    results[0].plot()[:, :, ::-1],
                    caption="Detección de seguridad",
                    use_container_width=True
                )

            else:
                st.success("✅ Área segura")
                st.image(img, use_container_width=True)

        else:
            st.warning("⚠️ Activa la alarma por voz para analizar intrusos")
            st.image(img, use_container_width=True)

    else:
        st.info("📷 Esperando captura de cámara...")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("Guardian Vision Pro | Interfaces Multimodales | Voz + IA + MQTT")
