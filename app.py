import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- Configuración de la página ---
st.set_page_config(page_title="Monitor de Burnout", page_icon="🧠", layout="wide")
st.title("🧠 Monitor de Salud Mental y Burnout Estudiantil")
st.markdown("Datos en vivo desde Supabase. Análisis basado en hábitos de estudio y estilo de vida.")

# --- Conexión a Supabase ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# --- Carga de datos desde Supabase ---
@st.cache_data(ttl=300)  # Cachea por 5 minutos
def cargar_estudiantes():
    try:
        response = supabase.table("estudiantes").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar estudiantes: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)  # Cachea por 1 minuto (las consultas cambian más seguido)
def cargar_consultas():
    try:
        response = supabase.table("consultas").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Convertir created_at a datetime
            if 'created_at' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar consultas: {e}")
        return pd.DataFrame()

df_estudiantes = cargar_estudiantes()
df_consultas = cargar_consultas()

if df_estudiantes.empty:
    st.warning("No se pudieron cargar los datos de estudiantes.")
    st.stop()

# --- Sidebar para navegación ---
st.sidebar.title("📂 Navegación")
vista = st.sidebar.radio(
    "Seleccioná una vista:",
    ["📊 Datos Históricos (300k estudiantes)", "📈 Consultas en Vivo (Formulario HTML)"]
)

# ======================== VISTA 1: DATOS HISTÓRICOS ========================
if vista == "📊 Datos Históricos (300k estudiantes)":
    st.header("📊 Análisis de la Población Estudiantil (Muestra de 300,000)")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Estudiantes", f"{len(df_estudiantes):,}")
    with col2:
        st.metric("Burnout Promedio", f"{df_estudiantes['puntaje_burnout'].mean():.2f}")
    with col3:
        st.metric("Horas de Sueño Promedio", f"{df_estudiantes['horas_sueño'].mean():.1f}")
    with col4:
        riesgo_alto = (df_estudiantes['nivel_riesgo'] == 'Alto').sum()
        st.metric("En Riesgo Alto", f"{riesgo_alto:,} ({riesgo_alto/len(df_estudiantes)*100:.1f}%)")

    col_izq, col_der = st.columns(2)
    with col_izq:
        st.subheader("Distribución por Nivel de Riesgo")
        df_riesgo = df_estudiantes['nivel_riesgo'].value_counts().reset_index()
        df_riesgo.columns = ['nivel_riesgo', 'cantidad']
        fig1 = px.pie(df_riesgo, values='cantidad', names='nivel_riesgo',
                      color='nivel_riesgo',
                      color_discrete_map={'Bajo':'green', 'Medio':'orange', 'Alto':'red'})
        st.plotly_chart(fig1, use_container_width=True)

    with col_der:
        st.subheader("Horas de Sueño vs. Puntaje de Burnout")
        fig2 = px.scatter(df_estudiantes, x='horas_sueño', y='puntaje_burnout', color='nivel_riesgo',
                          opacity=0.6, color_discrete_map={'Bajo':'green', 'Medio':'orange', 'Alto':'red'})
        fig2.update_layout(xaxis_title="Horas de Sueño", yaxis_title="Puntaje de Burnout")
        st.plotly_chart(fig2, use_container_width=True)

# ======================== VISTA 2: CONSULTAS EN VIVO ========================
else:
    st.header("📈 Consultas Recibidas desde el Test de Burnout")

    if df_consultas.empty:
        st.info("Aún no hay consultas registradas. ¡Probá el test para empezar a recolectar datos!")
        st.markdown("👉 [Realizá el test acá](https://33674727-cpu.github.io/DSIA/formulario.html)")
        st.stop()

    # Métricas de consultas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Tests Realizados", len(df_consultas))
    with col2:
        ultimo = df_consultas['created_at'].max().strftime("%d/%m %H:%M") if not df_consultas.empty else "N/A"
        st.metric("Última consulta", ultimo)
    with col3:
        alto = (df_consultas['nivel'] == 'Alto').sum()
        st.metric("Riesgo Alto", f"{alto} ({alto/len(df_consultas)*100:.1f}%)")
    with col4:
        st.metric("Puntaje Promedio", f"{df_consultas['puntaje'].mean():.1f} / 8")

    # Gráficos
    col_izq, col_der = st.columns(2)
    with col_izq:
        st.subheader("Distribución de Niveles de Riesgo (Consultas)")
        df_nivel = df_consultas['nivel'].value_counts().reset_index()
        df_nivel.columns = ['nivel', 'cantidad']
        fig3 = px.pie(df_nivel, values='cantidad', names='nivel',
                      color='nivel',
                      color_discrete_map={'Bajo':'green', 'Medio':'orange', 'Alto':'red'})
        st.plotly_chart(fig3, use_container_width=True)

    with col_der:
        st.subheader("Promedio de Horas de Sueño por Nivel")
        df_sueño = df_consultas.groupby('nivel')['horas_sueño'].mean().reset_index()
        fig4 = px.bar(df_sueño, x='nivel', y='horas_sueño', color='nivel',
                      color_discrete_map={'Bajo':'green', 'Medio':'orange', 'Alto':'red'})
        fig4.update_layout(yaxis_title="Horas de Sueño Promedio")
        st.plotly_chart(fig4, use_container_width=True)

    # Evolución temporal (si hay más de una consulta)
    if len(df_consultas) > 1:
        st.subheader("Evolución del Puntaje de Riesgo en el Tiempo")
        df_consultas_sorted = df_consultas.sort_values('created_at')
        fig5 = px.line(df_consultas_sorted, x='created_at', y='puntaje',
                       markers=True, title="Cada punto representa una consulta")
        fig5.update_layout(xaxis_title="Fecha y hora", yaxis_title="Puntaje de Riesgo")
        st.plotly_chart(fig5, use_container_width=True)

    # Tabla de últimas consultas
    st.subheader("Últimas 10 consultas recibidas")
    st.dataframe(df_consultas[['created_at', 'horas_sueño', 'estres_financiero', 'apoyo_social', 'horas_estudio', 'puntaje', 'nivel']]
                 .sort_values('created_at', ascending=False).head(10),
                 use_container_width=True)

    # Enlace al test
    st.markdown("---")
    st.markdown("👉 **[Realizá el test de burnout y sumá tu resultado a estas estadísticas](https://33674727-cpu.github.io/DSIA/formulario.html)**")

# --- Pie de página común ---
st.markdown("---")
st.caption("Dashboard creado con Streamlit y Supabase. Datos del dataset 'Student Mental Health and Burnout' y del formulario de predicción.")