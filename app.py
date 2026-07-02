"""
Agente Financiero CNBS
Analista virtual de indicadores financieros del sistema bancario hondureño.

Arquitectura:
- Datos: CSV con indicadores oficiales de la CNBS (16 bancos, 7,046 registros)
- Motor de consulta: Agente Pandas (LangChain) para análisis exacto sobre datos tabulares
- LLM desarrollo: Groq llama-3.3-70b-versatile / LLM producción: Gemini 2.5 Flash
- Interfaz: Streamlit
- Despliegue: Oracle Cloud Infrastructure (OCI) - Always Free VM

Decisión técnica: Groq durante desarrollo por capa gratuita generosa y velocidad.
Para producción se usa Gemini 2.5 Flash por mayor precisión y estabilidad.

Autor: Fausto Soto Euraque - Euraque Analytics
"""

import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_experimental.agents import create_pandas_dataframe_agent

load_dotenv()

# ============================================================
# CONFIGURACIÓN DEL MODELO
# True = Gemini 2.5 Flash (producción)
# False = Groq llama-3.3-70b-versatile (desarrollo)
# ============================================================
USE_GEMINI = True

if USE_GEMINI:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )
else:
    from langchain_groq import ChatGroq
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile",
        temperature=0
    )

# ============================================================
# CONTEXTO DEL SISTEMA
# ============================================================
CONTEXTO_SISTEMA = """
Eres un analista financiero especializado en el sistema bancario de Honduras.
Tienes acceso a un DataFrame de pandas llamado df con indicadores financieros
oficiales de la CNBS (Comision Nacional de Bancos y Seguros) de 16 bancos
comerciales hondurenos.

SIEMPRE debes ejecutar codigo Python real sobre el DataFrame para responder.
NUNCA sugieras codigo sin ejecutarlo - tienes acceso directo a los datos en df.

Columnas: Banco, FechaReporte, Indicador, CategoriaIndicador, Saldo

NOMBRES EXACTOS DE BANCOS (usa exactamente estos al filtrar):
BANCOCCI, BANHCAFE, HONDURAS, FICENSA, BANPAIS, BANCOS, FICOHSA, PROMERICA,
BANCO DAVIVIENDA, BAC CREDOMATIC, BANCO POPULAR, BANRURAL, BANCATLAN,
LAFISE, CUSCATLAN HONDURAS, AZTECA

REGLAS IMPORTANTES:
- FICOHSA y FICENSA son bancos DIFERENTES. No los confundas nunca.
  Si tienes duda del nombre exacto, usa df["Banco"].unique() para verificar.
- Si una busqueda con nombre exacto no encuentra resultados, usa
  df["Indicador"].str.contains("palabra clave", case=False) en lugar de ==
  para evitar fallos por tildes o mayusculas.
- "BANCOS" y "HONDURAS" son agregados del sistema completo, no bancos individuales.
- Valores negativos en ROA y ROE indican perdidas del periodo, son datos reales.
- Valores altos en Cobertura de Mora (>100%) son normales e indican buena cobertura.
- AZTECA tiene perfil atipico (microfinanzas/alto riesgo): tasas y spread muy altos,
  mayor morosidad. Aclaralo si aparece como valor extremo en comparaciones.
- Cuando pregunten por el mayor o menor indicador en un periodo, usa el PROMEDIO
  (.mean()) de todos los registros de ese periodo, no la suma (.sum()).
- Responde siempre en espanol con precision numerica y contexto financiero claro.
- Si comparas bancos, ordenalos de mayor a menor en el indicador solicitado.
- Explica brevemente el contexto financiero de tu respuesta en 2-3 oraciones.
"""

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/indicadores_financieros_CNBS.csv")
    return df

# ============================================================
# CREACIÓN DEL AGENTE
# ============================================================
@st.cache_resource
def crear_agente(_df):
    agente = create_pandas_dataframe_agent(
        llm=llm,
        df=_df,
        verbose=True,
        agent_type="zero-shot-react-description",
        allow_dangerous_code=True,
        prefix=CONTEXTO_SISTEMA
    )
    return agente

# ============================================================
# INTERFAZ STREAMLIT
# ============================================================
st.set_page_config(
    page_title="Agente Financiero CNBS",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Agente Financiero CNBS")
st.caption("Analista virtual de indicadores financieros del sistema bancario hondureño")

df = cargar_datos()
agente = crear_agente(df)

# Sidebar
with st.sidebar:
    st.subheader("Dataset")
    st.metric("Registros", f"{len(df):,}")
    st.metric("Bancos", df['Banco'].nunique())
    st.metric("Indicadores", df['Indicador'].nunique())
    st.caption(f"Período: {df['FechaReporte'].min()} a {df['FechaReporte'].max()}")
    st.divider()
    st.caption("Fuente: Comisión Nacional de Bancos y Seguros (CNBS)")
    st.caption(f"Modelo: {'Gemini 2.5 Flash' if USE_GEMINI else 'Groq llama-3.3-70b'}")

# Historial de chat
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        {
            "role": "assistant",
            "content": "Hola. Soy tu analista financiero del sistema bancario hondureño. Pregúntame sobre solvencia, morosidad, liquidez o rentabilidad de cualquier banco comercial."
        }
    ]

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

# Preguntas sugeridas
st.write("**Preguntas sugeridas:**")
col1, col2, col3 = st.columns(3)
pregunta_sugerida = None

with col1:
    if st.button("¿Mayor morosidad en 2025?"):
        pregunta_sugerida = "¿Qué banco tiene el mayor índice de morosidad sobre cartera crediticia total en 2025?"
with col2:
    if st.button("ROA de Ficohsa"):
        pregunta_sugerida = "¿Cuál fue el ROA de Ficohsa en 2025?"
with col3:
    if st.button("Solvencia sobre el mínimo"):
        pregunta_sugerida = "¿Qué bancos tienen índice de adecuación de capital por encima del 14% en 2025?"

# Input
pregunta_usuario = st.chat_input("Escribe tu pregunta sobre el sistema bancario hondureño...")
pregunta_final = pregunta_sugerida or pregunta_usuario

if pregunta_final:
    st.session_state.mensajes.append({"role": "user", "content": pregunta_final})
    with st.chat_message("user"):
        st.markdown(pregunta_final)

    with st.chat_message("assistant"):
        with st.spinner("Analizando indicadores..."):
            try:
                respuesta = agente.invoke(pregunta_final)
                texto_respuesta = respuesta['output']
            except Exception as e:
                texto_respuesta = f"Error al procesar la consulta: {str(e)}"
            st.markdown(texto_respuesta)

    st.session_state.mensajes.append({"role": "assistant", "content": texto_respuesta})
