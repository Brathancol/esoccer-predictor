import streamlit as st
import json
import os

# ==========================================
# CONFIGURACIÓN DE ESTILO
# ==========================================
st.set_page_config(page_title="Esoccer Predictor Pro", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Poppins:wght@400;600;800&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        font-family: 'Poppins', sans-serif;
    }
    
    p, span, label, div {
        color: #ffffff !important;
    }
    
    h1, h2, h3, h4, h5 {
        font-family: 'Orbitron', sans-serif !important;
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
    }
    
    .stRadio [role="radiogroup"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 10px !important;
    }
    
    .stRadio [role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #00ff88;
        border-radius: 10px;
        padding: 5px 10px;
        color: #ffffff;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        margin: 0;
    }
    
    .stRadio [role="radiogroup"] label:hover {
        background: rgba(0, 255, 136, 0.2);
    }
    
    .stRadio [role="radiogroup"] label:has(input:checked) {
        background: #00ff88;
        color: #000000 !important;
    }
    
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
    }
    
    div[data-testid="stMetric"] label {
        color: #a0aec0 !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.5rem;
        color: #00ff88 !important;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00ff88, #00b4d8, #ff0055) !important;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
    }
    
    .stAlert {
        background-color: rgba(255, 0, 85, 0.2) !important;
        border: 1px solid #ff0055 !important;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(255, 0, 85, 0.3);
    }
    
    .titulo-principal {
        background: linear-gradient(90deg, #00ff88, #00b4d8, #ff0055);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .seccion-titulo {
        background: linear-gradient(90deg, #00ff88, #00b4d8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.8rem;
        font-weight: 800;
        margin-top: 20px;
    }
    
    .linea-apuesta {
        font-size: 1.4rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# FUNCIONES PARA LEER JUGADORES DE ARCHIVOS
# ==========================================
def leer_jugadores_8m():
    with open("jugadores_8m.txt", "r", encoding="utf-8") as f:
        return [linea.strip() for linea in f.readlines() if linea.strip()]

def leer_jugadores_12m():
    with open("jugadores_12m.txt", "r", encoding="utf-8") as f:
        return [linea.strip() for linea in f.readlines() if linea.strip()]

JUGADORES_8M = leer_jugadores_8m()
JUGADORES_12M = leer_jugadores_12m()

# ==========================================
# FUNCIONES
# ==========================================
def leer_datos_json(liga):
    if liga == "8m":
        archivo = "datos_json/ultimos_datos_8m.json"
    else:
        archivo = "datos_json/ultimos_datos_12m.json"
    
    if not os.path.exists(archivo):
        st.warning(f"⚠️ No existe el archivo {archivo}. Ejecuta primero el sistema de extracción.")
        return {}
    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)

def limpiar_equipo(nombre_equipo):
    if "ESOCCERBET" in nombre_equipo.upper():
        nombre_equipo = nombre_equipo.replace("ESOCCERBET.ORG", "").replace("ESOCCERBET", "").strip()
    return nombre_equipo.strip()

def obtener_equipos_para_jugador(jugador, datos):
    # ✅ CORRECCIÓN: Si el jugador tiene datos propios, buscar SOLO ahí
    if jugador in datos:
        equipos = set()
        for p in datos[jugador]:
            if p['equipo_jugador'] != "Sin equipo":
                equipos.add(limpiar_equipo(p['equipo_jugador']))
        return list(equipos)
    
    # Si NO tiene datos propios, buscar en donde fue rival
    equipos = set()
    for otros_jugadores, partidos in datos.items():
        for p in partidos:
            if p['rival'].lower() == jugador.lower():
                if p['equipo_rival'] != "Sin equipo":
                    equipos.add(limpiar_equipo(p['equipo_rival']))
    return list(equipos)

def obtener_partidos_por_equipo_avanzado(jugador, equipo, datos):
    # ✅ CORRECCIÓN: Si el jugador tiene datos propios, usar SOLO sus datos
    if jugador in datos:
        partidos = []
        for p in datos[jugador]:
            if limpiar_equipo(p['equipo_jugador']).lower() == equipo.lower():
                partidos.append(p)
        return partidos
    
    # Si NO tiene datos propios, buscar SOLO donde fue rival
    partidos = []
    for otros_jugadores, partidos_otros in datos.items():
        if otros_jugadores.lower() == jugador.lower():
            continue
        
        for p in partidos_otros:
            if p['rival'].lower() == jugador.lower() and limpiar_equipo(p['equipo_rival']).lower() == equipo.lower():
                partidos.append({
                    "fecha": p['fecha_partido'],
                    "estado": p['estado'],
                    "rival": otros_jugadores,
                    "equipo_jugador": limpiar_equipo(p['equipo_rival']),
                    "equipo_rival": limpiar_equipo(p['equipo_jugador']),
                    "goles_jugador": p['goles_rival'],
                    "goles_rival": p['goles_jugador'],
                    "resultado": "Victoria" if p['goles_rival'] > p['goles_jugador'] else ("Derrota" if p['goles_rival'] < p['goles_jugador'] else "Empate"),
                    "fecha_partido": p['fecha_partido']
                })
    
    # Eliminar duplicados
    vistos = set()
    partidos_unicos = []
    for p in partidos:
        clave = f"{p['fecha_partido']}|{p['goles_jugador']}-{p['goles_rival']}|{p['equipo_rival']}"
        if clave not in vistos:
            vistos.add(clave)
            partidos_unicos.append(p)
    
    partidos_unicos.sort(key=lambda x: x['fecha_partido'], reverse=True)
    return partidos_unicos

def obtener_rivales(jugador, datos):
    partidos = datos.get(jugador, [])
    rivales = [p['rival'] for p in partidos if p['rival'] != "Sin equipo" and p['rival'] != "Desconocido"]
    return list(set(rivales))

def obtener_todos_enfrentamientos(jugador_a, jugador_b, datos):
    partidos_a = datos.get(jugador_a, [])
    partidos_a.sort(key=lambda x: x['fecha_partido'], reverse=True)
    enfrentamientos = []
    for p in partidos_a[:30]:
        if p['rival'].lower() == jugador_b.lower():
            enfrentamientos.append({
                "fecha": p['fecha_partido'],
                "jugador_a": jugador_a,
                "jugador_b": jugador_b,
                "jugador_a_equipo": limpiar_equipo(p['equipo_jugador']),
                "jugador_b_equipo": limpiar_equipo(p['equipo_rival']),
                "goles_a": p['goles_jugador'],
                "goles_b": p['goles_rival'],
                "resultado": p['resultado']
            })
    enfrentamientos.sort(key=lambda x: x['fecha'], reverse=True)
    return enfrentamientos

def calcular_h2h_detallado(jugador_a, jugador_b, datos):
    enfrentamientos = obtener_todos_enfrentamientos(jugador_a, jugador_b, datos)
    if len(enfrentamientos) == 0:
        return {"jugados": 0, "a_gana": 0, "b_gana": 0, "empates": 0, "goles_a": 0, "goles_b": 0, "promedio_goles": 0, "enfrentamientos": []}
    a_gana = sum(1 for e in enfrentamientos if e['resultado'] == 'Victoria')
    b_gana = sum(1 for e in enfrentamientos if e['resultado'] == 'Derrota')
    empates = sum(1 for e in enfrentamientos if e['resultado'] == 'Empate')
    goles_a = sum(e['goles_a'] for e in enfrentamientos)
    goles_b = sum(e['goles_b'] for e in enfrentamientos)
    return {
        "jugados": len(enfrentamientos),
        "a_gana": a_gana,
        "b_gana": b_gana,
        "empates": empates,
        "goles_a": goles_a,
        "goles_b": goles_b,
        "promedio_goles": (goles_a + goles_b) / len(enfrentamientos),
        "enfrentamientos": enfrentamientos
    }

def calcular_estadisticas(partidos):
    total = len(partidos)
    if total == 0:
        return {"total": 0, "victorias": 0, "derrotas": 0, "empates": 0, "win_rate": 0, "goles_favor": 0, "goles_contra": 0, "promedio_goles_favor": 0, "promedio_goles_contra": 0}
    victorias = sum(1 for p in partidos if p['resultado'] == 'Victoria')
    derrotas = sum(1 for p in partidos if p['resultado'] == 'Derrota')
    empates = sum(1 for p in partidos if p['resultado'] == 'Empate')
    goles_favor = sum(p['goles_jugador'] for p in partidos)
    goles_contra = sum(p['goles_rival'] for p in partidos)
    return {
        "total": total,
        "victorias": victorias,
        "derrotas": derrotas,
        "empates": empates,
        "win_rate": (victorias / total) * 100,
        "goles_favor": goles_favor,
        "goles_contra": goles_contra,
        "promedio_goles_favor": goles_favor / total,
        "promedio_goles_contra": goles_contra / total
    }

def calcular_goles_esperados(partidos_a, partidos_b):
    stats_a = calcular_estadisticas(partidos_a)
    stats_b = calcular_estadisticas(partidos_b)
    ataque_a = stats_a['promedio_goles_favor']
    ataque_b = stats_b['promedio_goles_favor']
    defensa_a = stats_a['promedio_goles_contra']
    defensa_b = stats_b['promedio_goles_contra']
    goles_esperados_a = (ataque_a + defensa_b) / 2
    goles_esperados_b = (ataque_b + defensa_a) / 2
    total_esperado = goles_esperados_a + goles_esperados_b
    return stats_a, stats_b, goles_esperados_a, goles_esperados_b, total_esperado

def calcular_probabilidad_over(total_esperado, linea):
    prob = max(0, min(100, ((total_esperado - linea) + 2.0) * 25))
    return prob

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.markdown('<h1 class="titulo-principal">⚽ ESOCCER PREDICTOR PRO</h1>', unsafe_allow_html=True)

# Selector de liga
st.markdown("### 🏆 Selecciona la Liga")
liga = st.selectbox("", ["8m", "12m"])
if liga == "8m":
    jugadores_disponibles = JUGADORES_8M
    lineas = [3.5, 4.5, 5.5, 6.5]
    etiqueta_liga = "8 minutos"
else:
    jugadores_disponibles = JUGADORES_12M
    lineas = [4.5, 5.5, 6.5, 7.5, 8.5]
    etiqueta_liga = "12 minutos"

datos = leer_datos_json(liga)

# ==========================================
# USANDO st.radio EN FORMATO HORIZONTAL
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔵 Jugador A")
    jugador_a = st.radio("Nombre:", jugadores_disponibles, key="jugador_a", horizontal=True)
    equipos_a = obtener_equipos_para_jugador(jugador_a, datos)
    if not equipos_a:
        equipos_a = ["Sin equipo"]
    equipo_a = st.radio("Equipo:", equipos_a, key="equipo_a", horizontal=True)

rivales = obtener_rivales(jugador_a, datos)
if not rivales:
    st.error(f"❌ {jugador_a} no tiene datos en la base de datos.")
    st.stop()

with col2:
    st.markdown("### 🔴 Jugador B")
    jugador_b = st.radio("Nombre:", rivales, key="jugador_b", horizontal=True)
    equipos_b = obtener_equipos_para_jugador(jugador_b, datos)
    if not equipos_b:
        equipos_b = ["Sin equipo"]
    equipo_b = st.radio("Equipo:", equipos_b, key="equipo_b", horizontal=True)

if jugador_a == jugador_b:
    st.error("❌ Los jugadores no pueden ser el mismo.")
    st.stop()

# ==========================================
# VALIDACIÓN DE ENFRENTAMIENTOS DIRECTOS
# ==========================================
h2h = calcular_h2h_detallado(jugador_a, jugador_b, datos)

if h2h['jugados'] == 0:
    st.error(f"❌ **{jugador_a} y {jugador_b} no tienen enfrentamientos directos en la base de datos.**")
    st.error("👉 **Por favor, elige otro jugador B** para que la predicción sea más precisa.")
    st.stop()

# ==========================================
# DATOS Y ESTADÍSTICAS
# ==========================================
partidos_a_equipo = obtener_partidos_por_equipo_avanzado(jugador_a, equipo_a, datos)
partidos_b_equipo = obtener_partidos_por_equipo_avanzado(jugador_b, equipo_b, datos)
stats_a, stats_b, goles_esperados_a, goles_esperados_b, total_esperado = calcular_goles_esperados(partidos_a_equipo, partidos_b_equipo)

# ==========================================
# TABLA DE ÚLTIMOS PARTIDOS
# ==========================================
st.markdown("---")
st.markdown('<h2 class="seccion-titulo">📊 ÚLTIMOS 5 PARTIDOS</h2>', unsafe_allow_html=True)

col_tabla1, col_tabla2 = st.columns(2)

with col_tabla1:
    st.write(f"**{jugador_a} - {equipo_a}**")
    ultimos_5_a = partidos_a_equipo[-5:]
    if ultimos_5_a:
        st.dataframe(
            [
                {
                    "Rival": p['rival'],
                    "Equipo Rival": limpiar_equipo(p['equipo_rival']),
                    "Goles": f"{p['goles_jugador']} - {p['goles_rival']}",
                    "Resultado": p['resultado'],
                    "Fecha": p['fecha_partido']
                }
                for p in ultimos_5_a
            ],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("No hay partidos recientes con este equipo.")

with col_tabla2:
    st.write(f"**{jugador_b} - {equipo_b}**")
    ultimos_5_b = partidos_b_equipo[-5:]
    if ultimos_5_b:
        st.dataframe(
            [
                {
                    "Rival": p['rival'],
                    "Equipo Rival": limpiar_equipo(p['equipo_rival']),
                    "Goles": f"{p['goles_jugador']} - {p['goles_rival']}",
                    "Resultado": p['resultado'],
                    "Fecha": p['fecha_partido']
                }
                for p in ultimos_5_b
            ],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("No hay partidos recientes con este equipo.")

# ==========================================
# SECCIÓN PRINCIPAL: PREDICCIONES OVER/UNDER
# ==========================================
st.markdown("---")
st.markdown('<h2 class="seccion-titulo">🔮 PREDICCIONES DE GOLES</h2>', unsafe_allow_html=True)
st.subheader(f"{jugador_a} ({equipo_a}) VS {jugador_b} ({equipo_b})")

col_metric1, col_metric2, col_metric3 = st.columns(3)

with col_metric1:
    st.metric(label=f"⚽ Goles esperados de {jugador_a}", value=f"{goles_esperados_a:.2f}")
with col_metric2:
    st.metric(label=f"⚽ Goles esperados de {jugador_b}", value=f"{goles_esperados_b:.2f}")
with col_metric3:
    st.metric(label="🎯 Total esperado en el partido", value=f"{total_esperado:.2f}")

st.markdown("---")
st.markdown(f"### 🎰 Líneas de apuestas ({etiqueta_liga})")

for linea in lineas:
    prob_over = calcular_probabilidad_over(total_esperado, linea)
    col_linea1, col_linea2 = st.columns([3, 1])
    
    with col_linea1:
        st.markdown(f'<div class="linea-apuesta">⚽ Más de {linea} goles</div>', unsafe_allow_html=True)
        st.progress(int(prob_over))
    
    with col_linea2:
        st.markdown(f'<div class="linea-apuesta">{prob_over:.1f}%</div>', unsafe_allow_html=True)
        st.write(f"*Menos de {linea}: {100 - prob_over:.1f}%*")

st.markdown("---")

# ==========================================
# HISTORIAL DIRECTO (ÚLTIMOS 10, CON DATAFRAME)
# ==========================================
st.markdown('<h2 class="seccion-titulo">🥊 HISTORIAL DIRECTO (H2H)</h2>', unsafe_allow_html=True)

if h2h['jugados'] > 0:
    col_h2h1, col_h2h2, col_h2h3 = st.columns(3)
    
    with col_h2h1:
        st.metric(label=f"✅ {jugador_a} gana", value=f"{h2h['a_gana']}")
    with col_h2h2:
        st.metric(label=f"❌ {jugador_b} gana", value=f"{h2h['b_gana']}")
    with col_h2h3:
        st.metric(label=f"🤝 Empates", value=f"{h2h['empates']}")
    
    # Promedio de goles como tarjeta métrica
    st.metric(label="🎯 Promedio de goles en sus enfrentamientos", value=f"{h2h['promedio_goles']:.2f}")
    
    # MOSTRAR SOLO LOS ÚLTIMOS 10 ENFRENTAMIENTOS
    st.markdown("#### 📋 Últimos 10 enfrentamientos")
    ultimos_10_h2h = h2h['enfrentamientos'][:10]
    
    st.dataframe(
        [
            {
                "Jugador A": e['jugador_a_equipo'] + " (" + e['jugador_a'] + ")",
                "Resultado": f"{e['goles_a']} - {e['goles_b']}",
                "Jugador B": e['jugador_b_equipo'] + " (" + e['jugador_b'] + ")",
                "Fecha": e['fecha']
            }
            for e in ultimos_10_h2h
        ],
        use_container_width=True,
        hide_index=True
    )