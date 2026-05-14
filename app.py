# =========================================================
# GUARDIAN VISION - CÓDIGO COMPLETO CON VOZ 
# =========================================================

import streamlit as st
import paho.mqtt.client as mqtt
import json
from PIL import Image
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Guardian Vision",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ESTILOS
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: white !important;
}

html, body, [class*="css"] {
    color: black !important;
}

section[data-testid="stSidebar"] {
    background-color: #f3f4f6 !important;
}

section[data-testid="stSidebar"] * {
    color: black !important;
}

.header-box {
    background: linear-gradient(90deg, #111827, #2563eb);
    padding: 25px;
    border-radius: 18px;
    text-align: center;
    color: white !important;
    margin-bottom: 20px;
}

.card {
    background-color: white;
    padding: 25px;
    border-radius: 18px;
    border: 2px solid #d1d5db;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.stButton > button {
    width: 100%;
    background-color: #2563eb !important;
    color: white !important;
    font-size: 18px !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 12px !important;
    margin-top: 8px !important;
}

div.bk-root {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="header-box">
    <h1>🛡️ GUARDIAN VISION</h1>
    <h3>Sistema Inteligente de Seguridad | Voz + Cámara + MQTT</h3>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.title("📘 Instrucciones")
    st.write("### 🎙️ Control por Voz")
    st.write("Presiona ESCUCHAR y di:")
    st.write("- enciende la alarma")
    st.write("- apaga la alarma")

    st.write("### 🔘 Control Manual")
    st.write("- Botón ENCENDER")
    st.write("- Botón APAGAR")

    st.write("### 📸 Vigilancia")
    st.write("Toma una foto para monitorear.")
    st.write("Si la alarma está activa, enviará alerta MQTT.")

# =========================================================
# MQTT
# =========================================================
BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "voice_ctrl"

@st.cache_resource
def setup_mqtt():
    client = mqtt.Client(client_id="ANGIE_GUARD")
    try:
        client.connect(BROKER, PORT, 60)
    except:
        pass
    return client

mqtt_client = setup_mqtt()

# =========================================================
# SESSION STATE
# =========================================================
if "alarma_activa" not in st.session_state:
    st.session_state.alarma_activa = False

if "ultimo_comando" not in st.session_state:
    st.session_state.ultimo_comando = "Sin comandos aún"

# =========================================================
# FUNCIÓN MQTT
# =========================================================
def enviar_mqtt(mensaje):
    try:
        payload = json.dumps({"Act1": mensaje})
        mqtt_client.publish(TOPIC, payload)
    except:
        pass

# =========================================================
# LAYOUT
# =========================================================
col1, col2 = st.columns([1, 2])

# =========================================================
# PANEL IZQUIERDO
# =========================================================
with col1:

    # ESTADO
    if st.session_state.alarma_activa:
        panel_bg = "#dcfce7"
        panel_border = "#16a34a"
        panel_text = "#166534"
        estado_texto = "🟢 ALARMA ACTIVADA"
    else:
        panel_bg = "#fee2e2"
        panel_border = "#dc2626"
        panel_text = "#991b1b"
        estado_texto = "🔴 ALARMA DESACTIVADA"

    # TÍTULO
    st.markdown(f"""
    <div style="
        background-color:{panel_bg};
        padding:25px;
        border-radius:18px;
        border:3px solid {panel_border};
        margin-bottom:20px;
    ">
        <h2 style="color:black; text-align:center;">🎙️ Control Inteligente</h2>
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # BOTÓN VOZ
    # =====================================================
    stt_button = Button(label="🎙️ ESCUCHAR", width=240, height=70)

    stt_button.js_on_event("button_click", CustomJS(code="""
        var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            alert("El navegador no soporta reconocimiento de voz");
        } else {
            var recognition = new SpeechRecognition();

            recognition.lang = 'es-ES';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onresult = function(e) {
                var value = e.results[0][0].transcript;

                document.dispatchEvent(
                    new CustomEvent("GET_TEXT", {
                        detail: value
                    })
                );
            };

            recognition.onerror = function(e) {
                console.log("Error:", e.error);
            };

            recognition.start();
        }
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=90,
        debounce_time=0
    )

    # =====================================================
    # PROCESAR VOZ CORREGIDO
    # =====================================================
    if result:
        st.write("DEBUG RESULTADO:", result)

        if "GET_TEXT" in result:
            comando = result.get("GET_TEXT", "").strip().lower()

            st.session_state.ultimo_comando = comando

            st.success(f"🎤 Se escuchó: {comando}")

            if (
                "enciende la alarma" in comando or
                "activar alarma" in comando or
                "enciende alarma" in comando or
                "activar" in comando or
                "encender" in comando
            ):
                st.session_state.alarma_activa = True
                enviar_mqtt("activado")
                st.success("🟢 Alarma ACTIVADA")

            elif (
                "apaga la alarma" in comando or
                "desactiva la alarma" in comando or
                "apaga alarma" in comando or
                "desactivar" in comando or
                "apagar" in comando
            ):
                st.session_state.alarma_activa = False
                enviar_mqtt("desactivado")
                st.warning("🔴 Alarma DESACTIVADA")

            else:
                st.error("⚠️ Comando no reconocido. Intenta de nuevo.")

    # =====================================================
    # ÚLTIMO COMANDO
    # =====================================================
    st.markdown("<h3 style='color:black;'>🗣️ Último comando:</h3>", unsafe_allow_html=True)
    st.info(st.session_state.ultimo_comando)

    # =====================================================
    # BOTONES MANUALES
    # =====================================================
    if st.button("🟢 ENCENDER ALARMA"):
        st.session_state.alarma_activa = True
        st.session_state.ultimo_comando = "Encendido manual"
        enviar_mqtt("activado")

    if st.button("🔴 APAGAR ALARMA"):
        st.session_state.alarma_activa = False
        st.session_state.ultimo_comando = "Apagado manual"
        enviar_mqtt("desactivado")

    # =====================================================
    # ESTADO DEL SISTEMA
    # =====================================================
    st.markdown(f"""
    <div style="
        background-color:{panel_bg};
        padding:20px;
        border-radius:15px;
        border:3px solid {panel_border};
        text-align:center;
        margin-top:20px;
    ">
        <h3 style="color:black;">📡 Estado del Sistema</h3>
        <h2 style="color:{panel_text};">{estado_texto}</h2>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# PANEL DERECHO - CÁMARA
# =========================================================
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown("<h2 style='color:black;'>📸 Cámara de Vigilancia</h2>", unsafe_allow_html=True)

    foto = st.camera_input("Toma una captura de seguridad")

    if foto is not None:
        imagen = Image.open(foto)

        st.image(imagen, caption="Captura actual", use_container_width=True)

        if st.session_state.alarma_activa:
            st.error("🚨 ALERTA: Presencia detectada")
            enviar_mqtt("intruso")
        else:
            st.success("✅ Monitoreo realizado (alarma apagada)")

    else:
        st.markdown(
            "<h3 style='color:black; text-align:center;'>📷 Esperando captura...</h3>",
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.markdown(
    "<p style='color:black; text-align:center;'>Guardian Vision © Proyecto Interfaces Multimodales | Angie Vargas - Isabella Saldarriaga - Salome Rivero</p>",
    unsafe_allow_html=True
)
