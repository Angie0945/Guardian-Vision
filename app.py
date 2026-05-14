import streamlit as st
import paho.mqtt.client as paho
import json
import numpy as np
import random
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
# ESTILOS VISUALES PREMIUM
# =========================================================
st.markdown("""
<style>

/* Fondo general */
.stApp {
    background-color: white;
}

/* Texto global negro */
html, body, [class*="css"], [class*="st-"] {
    color: black !important;
}

/* Sidebar clara */
section[data-testid="stSidebar"] {
    background-color: #f2f2f2 !important;
    color: black !important;
}

/* Encabezado principal */
.main-header {
    background: linear-gradient(90deg, #0f2027, #203a43, #2c5364);
    padding: 30px;
    border-radius: 18px;
    text-align: center;
    color: white !important;
    margin-bottom: 25px;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.25);
}

.main-header h1 {
    color: white !important;
    font-size: 48px;
    margin-bottom: 8px;
}

.main-header p {
    color: white !important;
    font-size: 20px;
}

/* Tarjetas */
.card {
    background-color: white;
    border-radius: 18px;
    padding: 25px;
    border: 2px solid #d9d9d9;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* Botones Streamlit */
.stButton>button {
    background-color: black !important;
    color: white !important;
    border-radius: 12px !important;
    font-size: 18px !important;
    font-weight: bold !important;
    padding: 12px !important;
    width: 100% !important;
}

/* Botón Bokeh */
div.bk-root {
    display: flex !important;
    justify-content: center !important;
    margin-top: 15px;
    margin-bottom: 15px;
}

/* Títulos */
h1, h2, h3 {
    color: black !important;
}

/* Cámara */
[data-testid="stCameraInput"] {
    border-radius: 15px;
    border: 2px solid #cccccc;
    padding: 10px;
}

/* Alertas */
.stAlert {
    border-radius: 12px;
}

/* Separadores */
hr {
    border: 1px solid #dddddd;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER PRINCIPAL
# =========================================================
st.markdown("""
<div class="main-header">
    <h1>🛡️ GUARDIAN VISION PRO</h1>
    <p>Seguridad Inteligente con Voz + Visión Artificial + MQTT</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("📘 Panel de Uso")
    st.write("""
### 🚀 Cómo funciona:

### 1️⃣ Activar:
Presiona **🎙️ ESCUCHAR**  
Di: **"enciende la alarma"**

### 2️⃣ Desactivar:
Di: **"apaga la alarma"**

### 3️⃣ Vigilancia:
Usa la cámara para monitoreo.

### 4️⃣ Respuesta:
- 🚨 Intruso detectado
- 🗣️ Alerta por voz
- 🌐 Señal MQTT
""")

    st.write("---")
    st.subheader("🧠 Innovación")
    st.write("""
**Guardian Vision utiliza software inteligente para potenciar hardware físico:**

📷 Cámara inteligente  
🎤 Control por voz  
🔊 Alarmas habladas  
🌐 Automatización IoT
""")

# =========================================================
# MQTT CONFIG
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
# MODELO YOLO
# =========================================================
@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")

model = load_model()

# =========================================================
# VARIABLES DE ESTADO
# =========================================================
if "alarma_activa" not in st.session_state:
    st.session_state.alarma_activa = False

# Frases de alarma
frases_alarma = [
    "⚠️ Atención. Intruso detectado.",
    "🚨 Zona protegida. Aléjese inmediatamente.",
    "🔴 Movimiento sospechoso registrado.",
    "🛑 Seguridad activada. Autoridades notificadas."
]

# =========================================================
# COLUMNAS PRINCIPALES
# =========================================================
col1, col2 = st.columns([1, 1.4])

# =========================================================
# PANEL IZQUIERDO - CONTROL DE VOZ
# =========================================================
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("🎤 Control por Voz")
    st.write("Presiona el botón y da una instrucción")

    # BOTÓN REAL
    stt_button = Button(
        label="🎙️ ESCUCHAR",
        width=320,
        height=90,
        button_type="primary"
    )

    stt_button.js_on_event("button_click", CustomJS(code="""
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            alert("Tu navegador no soporta reconocimiento de voz. Usa Google Chrome.");
            return;
        }

        var recognition = new SpeechRecognition();

        recognition.lang = 'es-ES';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onresult = function(event) {
            var texto = event.results[0][0].transcript;

            document.dispatchEvent(
                new CustomEvent("GET_TEXT", {
                    detail: texto
                })
            );
        };

        recognition.onerror = function(event) {
            alert("Error con el micrófono: " + event.error);
        };

        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="voice_command",
        refresh_on_update=False,
        override_height=120,
        debounce_time=0
    )

    # PROCESAMIENTO DE VOZ
    if result and "GET_TEXT" in result:

        comando = result["GET_TEXT"].lower().strip()

        st.success(f"🗣️ Comando detectado: {comando}")

        if "enciende la alarma" in comando or "activar" in comando:
            st.session_state.alarma_activa = True

            mqtt_client.publish(
                "voice_ctrl",
                json.dumps({"Act1": "activado"})
            )

            st.error("🔴 ALARMA ACTIVADA")

        elif "apaga la alarma" in comando or "desactivar" in comando:
            st.session_state.alarma_activa = False

            mqtt_client.publish(
                "voice_ctrl",
                json.dumps({"Act1": "desactivado"})
            )

            st.success("🟢 ALARMA DESACTIVADA")

        else:
            st.warning("⚠️ Comando no reconocido")

    # BOTONES MANUALES
    st.write("### 🎛️ Control Manual")

    if st.button("🔴 Activar Alarma"):
        st.session_state.alarma_activa = True
        mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "activado"}))

    if st.button("🟢 Desactivar Alarma"):
        st.session_state.alarma_activa = False
        mqtt_client.publish("voice_ctrl", json.dumps({"Act1": "desactivado"}))

    st.write("---")

    # ESTADO VISUAL
    if st.session_state.alarma_activa:
        st.error("🔴 SISTEMA ACTIVO")
    else:
        st.success("🟢 SISTEMA APAGADO")

    st.info("""
📘 Instrucciones:
1️⃣ Presiona ESCUCHAR  
2️⃣ Di “enciende la alarma”  
3️⃣ Usa cámara para vigilancia
""")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# PANEL DERECHO - CÁMARA + IA
# =========================================================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("📸 Cámara Inteligente")

    img_buffer = st.camera_input("Monitoreo en tiempo real")

    if img_buffer:

        img = Image.open(img_buffer).convert("RGB")

        if st.session_state.alarma_activa:

            with st.spinner("🔍 Analizando entorno..."):
                results = model(np.array(img), conf=0.4)

            detecciones = [
                model.names[int(box.cls)]
                for box in results[0].boxes
            ]

            if "person" in detecciones:

                frase = random.choice(frases_alarma)

                st.error("🚨 ¡INTRUSO DETECTADO!")
                st.warning(frase)

                mqtt_client.publish(
                    "voice_ctrl",
                    json.dumps({
                        "Act1": "INTRUSO",
                        "Mensaje": frase
                    })
                )

                st.image(
                    results[0].plot()[:, :, ::-1],
                    caption="Detección de Seguridad",
                    use_container_width=True
                )

            else:
                st.success("✅ Área segura")
                st.image(
                    img,
                    caption="Sin amenazas detectadas",
                    use_container_width=True
                )

        else:
            st.warning("⚠️ Activa el sistema para vigilancia avanzada")
            st.image(
                img,
                caption="Vista de cámara",
                use_container_width=True
            )

    else:
        st.info("📷 Esperando imagen de monitoreo...")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption("🛡️ Guardian Vision Pro | Interfaces Multimodales | Voz + IA + Seguridad Física")
