"""
Agente Financiero CNBS v2.1
Analista virtual oficial de indicadores financieros del sistema bancario hondureño.

Arquitectura Limpia y Homologada:
- Interfaz: Streamlit
- Motor: LangChain Dataframe Agent (Orquestador oficial)
- LLM: Groq (llama-3.3-70b-versatile)
- Datos: CSV oficial de la CNBS indexado en memoria como Datetime
- Caché: Respuestas por sesión para ahorrar tokens de Groq

Autor: Fausto Soto Euraque 
"""

import os
import time
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_experimental.agents import create_pandas_dataframe_agent

# Cargar variables de entorno (.env)
load_dotenv()

# ============================================================
# 1. CONFIGURACIÓN DEL MODELO DE LENGUAJE (GROQ)
# ============================================================
if not os.getenv("GROQ_API_KEY"):
    st.error("⚠️ La variable GROQ_API_KEY no está configurada en el entorno o archivo .env")
    st.stop()

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0  # Determinismo financiero absoluto
)

# ============================================================
# 2. CARGA Y PREPARACIÓN OPTIMIZADA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    # Nota: Asegúrate de mantener la ruta correcta según tu estructura local o en OCI
    ruta_csv = "data/indicadores_financieros_CNBS.csv"
    if not os.path.exists(ruta_csv):
        # Fallback por si ejecutas directamente en la raíz de la app
        ruta_csv = "indicadores_financieros_CNBS.csv"

    df = pd.read_csv(ruta_csv)
    # Conversión crítica a Datetime para habilitar la lógica nativa .dt.year en el agente
    df['FechaReporte'] = pd.to_datetime(df['FechaReporte'])
    return df

df = cargar_datos()

# ============================================================
# 3. PROMPT DE INGENIERÍA PARA EL AGENTE DE LANGCHAIN
# ============================================================
CONTEXTO_SISTEMA = """
Eres un analista financiero experto en el sistema bancario de Honduras.
Trabajas directamente sobre el DataFrame llamado 'df', el cual contiene los datos oficiales de la CNBS.

================================================================
REGLAS CRÍTICAS DE EJECUCIÓN (SÍGUELAS AL PIE DE LA LETRA)
================================================================
1. BÚSQUEDA FLEXIBLE DE INDICADORES (OBLIGATORIO):
   - Los nombres de los indicadores en el dataset contienen tildes. QUEDA PROHIBIDO usar la igualdad exacta (==) para la columna 'Indicador'.
   - Debes usar SIEMPRE '.str.contains()' con 'case=False' y raíces de palabras sin llegar a la tilde para evitar fallos:
     * Para Adecuación de Capital usa: df['Indicador'].str.contains('ADECUAC', case=False)
     * Para ROA usa: df['Indicador'].str.contains('ROA', case=False)
     * Para ROE usa: df['Indicador'].str.contains('ROE', case=False)
     * Para Morosidad usa: df['Indicador'].str.contains('MOROSIDAD', case=False)

2. PROHIBIDO RECREAR EL DATAFRAME: 
   - NUNCA escribas 'df = pd.DataFrame(...)' ni inventes datos ficticios. Usa el 'df' global que ya está en memoria y tiene miles de registros reales.

3. FORMATO NUMÉRICO:
   - Los valores de la columna 'Saldo' ya están expresados como porcentajes en el archivo (ej. 14.50 significa 14.50%). 
   - NO multipliques por 100 el resultado de las medias. Simplemente extrae la media (.mean()).

4. EXCLUSIÓN DE AGREGADOS:
   - Excluye siempre 'BANCOS' y 'HONDURAS' en comparaciones, listas o rankings individuales usando: ~df['Banco'].isin(['BANCOS', 'HONDURAS'])
   - Si el usuario pide explícitamente analizar 'el sistema' o 'el sistema bancario', incluye únicamente los agregados correspondientes.
   - Si piden 'bac', busca 'BAC CREDOMATIC' usando .str.contains('BAC', case=False).
   - AZTECA es un banco de microfinanzas con perfiles de riesgo más altos (tasas y morosidad mayores). Menciónalo si aparece como valor extremo.
"""

SUFFIX_SOLUCION = """
INSTRUCCIÓN FINAL DE CÓDIGO:
- Para obtener los datos de todo un año, filtra estrictamente con: df['FechaReporte'].dt.year == 2025
- Para rankings o listas por encima de un valor, primero agrupa y calcula la media anual: groupby('Banco')['Saldo'].mean()
- Luego aplica el filtro numérico correspondiente al promedio obtenido.
- Responde de forma muy analítica y fluida en español, ordenando los resultados de mayor a menor y limitando los números de la respuesta final a un máximo de 2 decimales.
"""

# ============================================================
# 4. INSTANCIACIÓN DEL AGENTE OFICIAL
# ============================================================
agente_cnbs = create_pandas_dataframe_agent(
    llm=llm,
    df=df,
    verbose=True,               # Permite monitorear las queries de Pandas en la consola del servidor (OCI/Local)
    agent_type="tool-calling",  # Arquitectura nativa y moderna basada en llamadas a funciones
    allow_dangerous_code=True,  # Requisito explícito de seguridad obligatorio de LangChain
    prefix=CONTEXTO_SISTEMA,
    suffix=SUFFIX_SOLUCION,
    max_iterations=5            # Cortafuegos para bucles infinitos
)

# ============================================================
# 5. CACHÉ DE RESPUESTAS POR SESIÓN
# ============================================================
if "cache_respuestas" not in st.session_state:
    st.session_state.cache_respuestas = {}

def consultar_con_cache(pregunta: str) -> str:
    """
    Consulta el agente con caché por sesión.
    Si la pregunta ya fue respondida, devuelve la respuesta cacheada sin gastar tokens.
    """
    clave = pregunta.strip().lower()

    if clave in st.session_state.cache_respuestas:
        return st.session_state.cache_respuestas[clave], True  # (respuesta, es_cache)

    # Ejecutar agente con retry
    respuesta_texto = ""
    for intento in range(3):
        try:
            resultado_agente = agente_cnbs.invoke({"input": pregunta})
            respuesta_texto = resultado_agente['output']
            break
        except Exception as e:
            if intento < 2:
                time.sleep(2)
                continue
            respuesta_texto = f"❌ Ocurrió un inconveniente al procesar la consulta. Error técnico: `{str(e)}`"
            break

    st.session_state.cache_respuestas[clave] = respuesta_texto
    return respuesta_texto, False  # (respuesta, es_cache)

# ============================================================
# 6. INTERFAZ GRÁFICA (STREAMLIT UI)
# ============================================================
st.set_page_config(
    page_title="Agente Financiero CNBS",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Agente Financiero CNBS")
st.caption("Analista virtual inteligente de indicadores financieros del sistema bancario hondureño")

# Configuración del Sidebar de control
with st.sidebar:
    st.subheader("Estado de Datos y Entorno")
    st.metric("Registros de la CNBS", f"{len(df):,}")
    st.metric("Bancos Indexados", df['Banco'].nunique())
    st.metric("Indicadores Financieros", df['Indicador'].nunique())

    # Formateo visual del rango de fechas
    fecha_min = df['FechaReporte'].min().strftime('%m/%Y')
    fecha_max = df['FechaReporte'].max().strftime('%m/%Y')
    st.caption(f"**Línea Temporal:** {fecha_min} a {fecha_max}")
    st.divider()

    # Métricas de caché
    st.metric("💾 Respuestas en caché", len(st.session_state.cache_respuestas))
    if st.button("🗑️ Limpiar caché", use_container_width=True):
        st.session_state.cache_respuestas.clear()
        st.success("Caché eliminado correctamente.")
        st.rerun()

    st.divider()
    st.caption("⚙️ **Infraestructura:** Oracle Cloud Infrastructure (OCI)")
    st.caption("🧠 **Modelo Core:** Llama 3.3 70B (Groq)")
    st.caption("👔 **Desarrollado por:** Euraque Analytics")

# Gestión y Persistencia del Historial de Chat
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        {
            "role": "assistant",
            "content": "¡Hola! Soy tu analista financiero especializado. Puedo calcular promedios anuales, generar rankings de solvencia, evaluar niveles de morosidad o comparar la rentabilidad (ROA/ROE) de cualquier banco comercial de Honduras con datos oficiales. ¿En qué indicador nos enfocamos hoy?"
        }
    ]

# Renderizar mensajes previos del chat
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

# Sección Inteligente de Preguntas Sugeridas
st.write("**Consultas Rápidas Financieras:**")
col1, col2, col3 = st.columns(3)
pregunta_sugerida = None

with col1:
    if st.button("📈 Mayor Morosidad 2025", use_container_width=True):
        pregunta_sugerida = "¿Qué banco tiene el mayor índice de morosidad sobre cartera crediticia total en 2025?"
with col2:
    if st.button("📊 ROA Ficohsa vs BAC 2025", use_container_width=True):
        pregunta_sugerida = "Compara el ROA de BAC Credomatic y Ficohsa en 2025"
with col3:
    if st.button("🛡️ Solvencia (Adecuación > 14%)", use_container_width=True):
        pregunta_sugerida = "¿Qué bancos tienen índice de adecuación de capital por encima del 14% en 2025?"

# Capturar Entrada de Usuario o Botón Sugerido
pregunta_usuario = st.chat_input("Escribe tu consulta sobre el sistema bancario...")
pregunta_final = pregunta_sugerida or pregunta_usuario

if pregunta_final:
    # Mostrar la pregunta en la interfaz
    st.session_state.mensajes.append({"role": "user", "content": pregunta_final})
    with st.chat_message("user"):
        st.markdown(pregunta_final)

    # Procesar consulta mediante el agente de LangChain (con caché)
    with st.chat_message("assistant"):
        respuesta_texto, es_cache = consultar_con_cache(pregunta_final)

        if es_cache:
            st.info("⚡ Respuesta recuperada desde caché (sin consumo de tokens).")
            st.markdown(respuesta_texto)
        else:
            with st.spinner("Calculando y ejecutando análisis financiero en tiempo real..."):
                if respuesta_texto.startswith("❌"):
                    st.error(respuesta_texto)
                else:
                    st.markdown(respuesta_texto)

    # Persistir la respuesta en el historial de sesión
    st.session_state.mensajes.append({"role": "assistant", "content": respuesta_texto})
