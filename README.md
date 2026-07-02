# 🏦 Agente Financiero CNBS

Analista virtual de indicadores financieros del sistema bancario hondureño, construido con LangChain, Pandas y Streamlit. Desplegado en Oracle Cloud Infrastructure (OCI).

---

## Descripción

**Agente Financiero CNBS** es un asistente conversacional que permite consultar 
en lenguaje natural los indicadores financieros oficiales de la Comisión Nacional 
de Bancos y Seguros (CNBS) de Honduras.

El agente tiene acceso a 7,046 registros de 16 bancos comerciales (enero 2024 - 
febrero 2026) y responde preguntas sobre solvencia, morosidad, rentabilidad, 
liquidez y cumplimiento regulatorio, ejecutando código Python real sobre los datos 
para garantizar precisión numérica.

Construido con LangChain + agente Pandas, Groq (desarrollo) y Gemini 2.0 Flash 
(producción), con interfaz Streamlit desplegada en Oracle Cloud Infrastructure.

---
## ¿Por qué datos de la CNBS?

El challenge permite usar cualquier documento. Se eligieron los indicadores 
oficiales de la CNBS por tres razones concretas:

1. **Relevancia sectorial:** Los 16 bancos comerciales hondureños están 
   obligados a reportar estos indicadores al regulador. Son los mismos datos 
   que usan los equipos de riesgo y cumplimiento de BAC, Ficohsa y Atlántida.

2. **Diferenciación:** Un agente que analiza datos regulatorios reales del 
   sistema bancario hondureño es más demostrable y memorable que uno sobre 
   ventas genéricas.

3. **Verificabilidad:** Los datos son públicos y descargables desde el sitio 
   oficial de la CNBS, lo que garantiza trazabilidad y reproducibilidad.

---
## Arquitectura

```
CSV Indicadores CNBS (7,046 registros)
        ↓
Pandas DataFrame
        ↓
Agente LangChain (zero-shot-react-description)
        ↓
Groq llama-3.1-8b-instant (desarrollo) / Gemini 2.5 Flash (producción)
        ↓
Interfaz Streamlit
        ↓
Deploy en Oracle Cloud Infrastructure (OCI)
```

---

## Decisiones técnicas

| Decisión | Opción elegida | Razón |
|----------|---------------|-------|
| Motor de consulta | Agente Pandas (LangChain) | Las preguntas son analíticas y exactas sobre datos tabulares, no búsqueda semántica en texto libre |
| LLM desarrollo | Groq llama-3.1-8b-instant | Capa gratuita generosa, permite múltiples iteraciones sin restricciones de cuota |
| LLM producción | Gemini 2.0 Flash | Mayor precisión en análisis de datos financieros estructurados |
| Formato de datos | CSV (convertido desde Excel CNBS) | Formato nativo para Pandas, sin problemas de extracción de tablas como en PDF |
| Agent type | zero-shot-react-description | Más estable con Groq que tool-calling; permite auto-corrección en errores de filtrado |

---

## Dataset

- **Fuente:** Comisión Nacional de Bancos y Seguros (CNBS) - Honduras
- **Registros:** 7,046
- **Bancos:** 16 bancos comerciales hondureños
- **Período:** Enero 2024 - Febrero 2026
- **Indicadores:** 17 indicadores en 6 categorías

| Categoría | Indicadores incluidos |
|-----------|----------------------|
| Solvencia | Índice de adecuación de capital |
| Calidad de Activos | Índice de morosidad sobre cartera crediticia total |
| Liquidez | Cobertura de mora, calces de moneda |
| Rentabilidad | ROA, ROE, tasa activa, spread de intermediación |
| Gestión | Gastos administrativos, eficiencia |
| Cumplimiento | Indicadores regulatorios CNBS |

---

## Ejemplos de preguntas y respuestas

| Pregunta | Respuesta |
|----------|-----------|
| ¿Qué banco tiene el mayor índice de morosidad en 2025? | BANCO POPULAR |
| ¿Cuál fue el ROA de Ficohsa en 2025? | 0.87% |
| ¿Qué bancos tienen adecuación de capital por encima del 14% en 2025? | BANCOCCI, FICENSA, AZTECA, PROMERICA, BANRURAL, HONDURAS, LAFISE, BANHCAFE, BANCO POPULAR, BANCOS |
| Diferencia entre el ROE de BAC Credomatic y Ficohsa en 2025 | 3.92% |

---

## Estructura del proyecto

```
agente-financiero-cnbs/
├── app.py                              # Aplicación principal (Streamlit + agente)
├── requirements.txt                    # Dependencias
├── .env.example                        # Plantilla de variables de entorno
├── data/
│   └── indicadores_financieros_CNBS.csv  # Dataset oficial CNBS
└── README.md
```

---

## Instrucciones para ejecutar localmente

**1. Clonar el repositorio**
```bash
git clone https://github.com/fsotoeu-cyber/agente-financiero-cnbs.git
cd agente-financiero-cnbs
```

**2. Instalar dependencias**
```bash
pip install -r requirements.txt
```

**3. Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus claves API
```

Contenido del `.env`:
```
GROQ_API_KEY=tu_clave_groq
GEMINI_API_KEY=tu_clave_gemini
```

**4. Ejecutar**
```bash
streamlit run app.py
```

**5. Abrir en el navegador**
```
http://localhost:8501
```

---

## Deploy en OCI

La aplicación está desplegada en una instancia VM Always Free de Oracle Cloud Infrastructure.

```bash
# En la VM de OCI
git clone https://github.com/fsotoeu-cyber/agente-financiero-cnbs.git
cd agente-financiero-cnbs
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

**URL pública:** `http://<IP_PUBLICA_OCI>:8501`

> Captura de pantalla del deploy en OCI — se actualizará al completar el despliegue.

---

## Tecnologías

- Python 3.10+
- [LangChain](https://www.langchain.com/) — framework de agentes
- [Streamlit](https://streamlit.io/) — interfaz web
- [Pandas](https://pandas.pydata.org/) — análisis de datos
- [Groq API](https://groq.com/) — LLM en desarrollo
- [Gemini 2.0 Flash](https://ai.google.dev/) — LLM en producción
- [Oracle Cloud Infrastructure](https://www.oracle.com/cloud/) — deploy

---

## Autor

**Fausto Soto Euraque**  
Tegucigalpa, Honduras  
[LinkedIn](https://www.linkedin.com/in/fsotoeu) | [GitHub](https://github.com/fsotoeu-cyber)

---

## Licencia

MIT
