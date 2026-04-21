import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- Configuración de la página ---
st.set_page_config(page_title="Monitor de Burnout", page_icon="🧠", layout="wide")
st.title("🧠 Monitor de Salud Mental y Burnout Estudiantil")
st.markdown("Datos en vivo desde Supabase. Análisis basado en hábitos de estudio y estilo de vida.")

# --- Conexión a Supabase ---
# Las credenciales se leen de los secretos de Streamlit Cloud
SUPABASE_URL = st.secrets["https://aeyatxhedhuimttvhnhk.supabase.co"]
SUPABASE_KEY = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFleWF0eGhlZGh1aW10dHZobmhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3ODI4NTksImV4cCI6MjA5MjM1ODg1OX0.y6C8bIONBWVD8qey-JFFv7H4EYsg57BAmS22yyXZ8-g"]

@st.cache_resource
def init_supabase() -> Client:
    """Inicializa el cliente de Supabase. La función se cachea para no recrear la conexión."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- Carga de datos desde Supabase ---
@st.cache_data(ttl=600) # Cachea los datos por 10 minutos
def cargar_datos():
    """Obtiene todos los registros de la tabla 'estudiantes'."""
    try:
        response = supabase.table("estudiantes").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("No se pudieron cargar los datos. Verifica tu conexión a Supabase.")
    st.stop()

# --- Métricas Principales (KPIs) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Estudiantes", len(df))
with col2:
    st.metric("Burnout Promedio", f"{df['puntaje_burnout'].mean():.2f}")
with col3:
    st.metric("Horas de Sueño Promedio", f"{df['horas_sueño'].mean():.1f}")
with col4:
    # Calculamos el % de estudiantes en riesgo alto
    riesgo_alto = (df['nivel_riesgo'] == 'Alto').sum()
    st.metric("En Riesgo Alto", f"{riesgo_alto} ({riesgo_alto/len(df)*100:.1f}%)")

# --- Gráficos Interactivos ---
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("Distribución por Nivel de Riesgo")
    # Convertir la serie a DataFrame para Plotly
    df_riesgo = df['nivel_riesgo'].value_counts().reset_index()
    df_riesgo.columns = ['nivel_riesgo', 'cantidad']
    fig1 = px.pie(df_riesgo, values='cantidad', names='nivel_riesgo',
                  color='nivel_riesgo',
                  color_discrete_map={'Bajo':'green', 'Medio':'orange', 'Alto':'red'})
    st.plotly_chart(fig1, use_container_width=True)

with col_der:
    st.subheader("Relación: Horas de Sueño vs. Puntaje de Burnout")
    fig2 = px.scatter(df, x='horas_sueño', y='puntaje_burnout', color='nivel_riesgo',
                      opacity=0.6, color_discrete_map={'Bajo':'green', 'Medio':'orange', 'Alto':'red'},
                      title="Menos horas de sueño se asocian a mayor riesgo")
    fig2.update_layout(xaxis_title="Horas de Sueño", yaxis_title="Puntaje de Burnout")
    st.plotly_chart(fig2, use_container_width=True)

# --- Pie de página ---
st.markdown("---")
st.caption("Dashboard creado con Streamlit y Supabase. Datos del dataset 'Student Mental Health and Burnout'.")