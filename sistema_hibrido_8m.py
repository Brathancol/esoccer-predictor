import asyncio
import random
import time
import os
import csv
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright

# ==========================================
# CONFIGURACIÓN (LIGA 8 MINUTOS)
# ==========================================
DURACION = "8m"

# ==========================================
# LISTA DE JUGADORES (Leyendo desde el archivo de texto)
# ==========================================
def leer_jugadores():
    with open("jugadores_8m.txt", "r", encoding="utf-8") as f:
        return [linea.strip() for linea in f.readlines() if linea.strip()]

def generar_urls(nombres):
    return [{"nombre": nombre, "url": f"https://esoccerbet.org/fifa-8-minutes/{nombre.lower()}/"} for nombre in nombres]

# ==========================================
# FUNCIONES DE LECTURA Y GUARDADO
# ==========================================
def guardar_en_csv(nombre_jugador, partidos):
    if not partidos: return
    if not os.path.exists("datos_csv/8m"): os.makedirs("datos_csv/8m")
    archivo_csv = f"datos_csv/8m/{nombre_jugador}.csv"
    archivo_existe = os.path.exists(archivo_csv)
    try:
        with open(archivo_csv, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not archivo_existe:
                writer.writerow(["Fecha_Extraccion", "Duración", "Nombre_Jugador", "Estado", "Rival", "Equipo_Jugador", "Equipo_Rival", "Goles_Jugador", "Goles_Rival", "Resultado", "Fecha_Partido"])
            fecha_extraccion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for p in partidos:
                writer.writerow([fecha_extraccion, DURACION, nombre_jugador, p['estado'], p['rival'], p['equipo_jugador'], p['equipo_rival'], p['goles_jugador'], p['goles_rival'], p['resultado'], p['fecha_partido']])
        print(f"💾 Guardado en Excel: datos_csv/8m/{nombre_jugador}.csv")
    except PermissionError:
        print(f"⚠️ ¡Cuidado! Tienes el archivo {nombre_jugador}.csv abierto en Excel. No se pudo guardar.")

def guardar_en_json(todos_los_datos):
    archivo = "datos_json/ultimos_datos_8m.json"
    historial_previo = {}
    
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                historial_previo = json.load(f)
        except:
            historial_previo = {}
    
    for jugador, partidos_nuevos in todos_los_datos.items():
        if jugador not in historial_previo:
            historial_previo[jugador] = []
        
        fechas_existentes = {p['fecha_partido'] for p in historial_previo[jugador]}
        
        for partido in partidos_nuevos:
            if partido['fecha_partido'] not in fechas_existentes:
                historial_previo[jugador].append(partido)
                fechas_existentes.add(partido['fecha_partido'])
    
    if not os.path.exists("datos_json"): os.makedirs("datos_json")
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(historial_previo, f, ensure_ascii=False, indent=4)
    print(f"💾 Historial acumulado guardado: {len(historial_previo)} jugadores, {sum(len(v) for v in historial_previo.values())} partidos en total")

def registrar_error(error):
    with open("errores_8m.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR: {error}\n")

# ==========================================
# FUNCIÓN DE EXTRACCIÓN
# ==========================================
async def extraer_datos():
    async with async_playwright() as p:
        print(f"🚀 Abriendo navegador (Liga {DURACION})...")
        
        # Configuración anti-detección
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--window-size=1920,1080'
            ]
        )
        
        # Crear contexto con User-Agent de Windows Chrome
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='es-ES',
            timezone_id='Europe/Madrid'
        )
        
        # Añadir scripts para ocultar que es un bot
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        
        nombres = leer_jugadores()
        jugadores = generar_urls(nombres)
        print(f"📋 Total de jugadores a monitorear: {len(jugadores)}")
        todos_los_datos = {}

        try:
            await page.goto("https://esoccerbet.org/app/", wait_until="domcontentloaded")
            await page.wait_for_timeout(random.randint(4000, 6000))
            
            try:
                await page.click("button:has-text('Aceptar')", timeout=3000)
            except:
                pass

            for jugador in jugadores:
                print(f"\n🔎 Entrando al perfil de {jugador['nombre']}...")
                try:
                    await page.goto(jugador['url'], wait_until="domcontentloaded")
                    
                    # Esperar un poco más para que cargue todo
                    await page.wait_for_timeout(random.randint(6000, 8000))
                    
                    # Scroll progresivo para forzar la carga
                    for i in range(8):
                        await page.mouse.wheel(0, 1500)
                        await page.wait_for_timeout(random.randint(800, 1200))
                    
                    await page.wait_for_timeout(4000)

                    print(f"📊 Leyendo datos de {jugador['nombre']}...")
                    
                    contenedores_partidas = await page.query_selector_all("div.partida")
                    
                    partidos_encontrados = []
                    contador = 0
                    
                    for contenedor in contenedores_partidas:
                        if contador >= 20: break
                        
                        texto = " ".join((await contenedor.inner_text()).split())
                        match = re.search(r'\((\d+)\)\s*(\d+)\s*-\s*(\d+)\s*\((\d+)\)', texto)
                        
                        if match:
                            goles_jugador = int(match.group(2))
                            goles_rival = int(match.group(3))
                            
                            fecha_match = re.search(r'(\d{2}/\d{2}\s+\d{2}:\d{2})', texto)
                            fecha_partido = fecha_match.group(1) if fecha_match else "Sin fecha"
                            
                            marcador_txt = match.group(0)
                            partes = texto.split(marcador_txt)
                            
                            lado_izq = partes[0].strip().split()
                            nombre_jugador_web = lado_izq[0] if lado_izq else jugador['nombre']
                            equipo_jugador = " ".join(lado_izq[1:]) if len(lado_izq) > 1 else "Sin equipo"
                            
                            lado_der_con_fecha = partes[-1].strip() if len(partes) > 1 else ""
                            lado_der = re.sub(r'\s*\d{2}/\d{2}\s+\d{2}:\d{2}', '', lado_der_con_fecha).strip()
                            
                            palabras_der = lado_der.split()
                            rival = palabras_der[0] if palabras_der else "Rival"
                            equipo_rival = " ".join(palabras_der[1:]) if len(palabras_der) > 1 else "Sin equipo"
                            
                            if goles_jugador > goles_rival: resultado = "Victoria"
                            elif goles_jugador < goles_rival: resultado = "Derrota"
                            else: resultado = "Empate"
                            
                            partido_data = {
                                'estado': 'Finalizado',
                                'rival': rival,
                                'equipo_jugador': equipo_jugador,
                                'equipo_rival': equipo_rival,
                                'goles_jugador': goles_jugador,
                                'goles_rival': goles_rival,
                                'resultado': resultado,
                                'fecha_partido': fecha_partido
                            }
                            
                            print(f"🎮 {nombre_jugador_web} ({equipo_jugador}) {goles_jugador}-{goles_rival} {rival} ({equipo_rival}) | {resultado} | {fecha_partido}")
                            partidos_encontrados.append(partido_data)
                            contador += 1
                    
                    todos_los_datos[jugador['nombre']] = partidos_encontrados
                    
                    if partidos_encontrados:
                        guardar_en_csv(jugador['nombre'], partidos_encontrados)
                    else:
                        print(f"ℹ️ No se encontraron partidos para {jugador['nombre']}.")

                except Exception as e:
                    print(f"⚠️ Error con {jugador['nombre']}: {e}")
                    registrar_error(f"Error con {jugador['nombre']}: {e}")

                await page.wait_for_timeout(random.randint(5000, 8000))

            guardar_en_json(todos_los_datos)

        except Exception as e:
            print(f"❌ Error fatal: {e}")
            registrar_error(f"Error fatal: {e}")
        finally:
            try:
                await browser.close()
            except:
                pass
            print("\n✅ Extracción finalizada!")

# ==========================================
# EJECUCIÓN (Solo una vez, sin bucle infinito)
# ==========================================
print(f"⏱️ Ejecutando extracción: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
asyncio.run(extraer_datos())
print("✅ Extracción finalizada!")