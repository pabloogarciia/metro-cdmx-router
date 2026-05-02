# =========================
# METRO CDMX - RUTEO CON FRECUENCIAS, PESOS Y TRANSBORDOS
# =========================

import pandas as pd
from datetime import datetime, time
from collections import defaultdict
import heapq
import math

# ---------- 0) CONFIGURACIÓN ----------
FILE_PATH = "IA - TIEMPOS TRASLADOS.xlsx"


# Tiempo que el tren permanece parado al llegar a una estación (min)
TIEMPO_PARADA_MIN = 0.5  # 30 segundos (ajústalo)

# Espera promedio por frecuencia: True => freq/2, False => freq completa
USAR_ESPERA_PROMEDIO = True

# Cuánto pesan los "pesos" en el f-score. 0 => solo minutos reales.
ALPHA_PESO = 0.1

# ---------- 1) FRECUENCIAS / PESOS (de tus tablas) ----------
FREQ_TABLE = {
    "sabado": {
        1: {"baja": (10, 100), "valle": (6, 60), "pico": (4, 40)},
        3: {"baja": (10, 100), "valle": (6, 60), "pico": (4, 40)},
        7: {"baja": (10, 100), "valle": (6, 60), "pico": (4, 40)},
        9: {"baja": (11, 110), "valle": (7, 70), "pico": (5, 50)},
        12: {"baja": (12, 120), "valle": (8, 80), "pico": (5, 50)},
    },
    "laborable": {
        1: {"baja": (7, 70), "valle": (4, 40), "pico": (2, 20)},
        3: {"baja": (7, 70), "valle": (4, 40), "pico": (2, 20)},
        7: {"baja": (8, 80), "valle": (5, 50), "pico": (3, 30)},
        9: {"baja": (7, 70), "valle": (4, 40), "pico": (2, 20)},
        12: {"baja": (9, 90), "valle": (5, 50), "pico": (3, 30)},
    },
    "domingo": {  # domingos y festivos
        1: {"baja": (10, 100), "valle": (8, 80), "pico": (6, 60)},
        3: {"baja": (10, 100), "valle": (8, 80), "pico": (6, 60)},
        7: {"baja": (11, 110), "valle": (9, 90), "pico": (7, 70)},
        9: {"baja": (10, 100), "valle": (8, 80), "pico": (6, 60)},
        12: {"baja": (12, 120), "valle": (10, 100), "pico": (8, 80)},
    },
}

TRAMOS_HORARIOS = {
    "laborable": {
        "pico":  [(time(6,0), time(9,0)), (time(18,0), time(21,0))],
        "valle": [(time(9,0), time(17,59,59)), (time(21,0), time(22,59,59))],
    },
    "sabado": {
        "pico":  [(time(6,0), time(9,0)), (time(18,0), time(21,0))],
        "valle": [(time(9,0), time(17,59,59))],
    },
    "domingo": {
        "pico":  [(time(18,0), time(20,59,59))],
        "valle": [(time(11,0), time(17,59,59))],
    }
}

def detectar_tramo(tipo_dia, hora):
    """tipo_dia: laborable|sabado|domingo, hora: datetime.time -> pico|valle|baja"""
    reglas = TRAMOS_HORARIOS[tipo_dia]
    for tramo in ("pico", "valle"):
        for ini, fin in reglas.get(tramo, []):
            if ini <= hora <= fin:
                return tramo
    return "baja"

def frecuencia_y_peso(linea, tipo_dia, hora):
    """Devuelve (frecuencia_min, peso) para esa línea en ese día/hora."""
    tramo = detectar_tramo(tipo_dia, hora)
    return FREQ_TABLE[tipo_dia][linea][tramo]

def tipo_dia_desde_fecha(dt):
    """Convierte datetime a tipo_dia."""
    wd = dt.weekday()  # 0=lunes ... 5=sábado 6=domingo
    if wd == 5:
        return "sabado"
    if wd == 6:
        return "domingo"
    return "laborable"

# ---------- 2) CARGA Y LIMPIEZA DEL EXCEL ----------
def cargar_datos_excel(path=FILE_PATH):
    xls = pd.ExcelFile(path)
    tiempos = pd.read_excel(path, sheet_name="TIEMPOS")
    trans = pd.read_excel(path, sheet_name="TRANSBORDOS")

    # ---- limpiar TIEMPOS ----
    col_map = {
        "Unnamed: 1":"linea",
        "Unnamed: 3":"est_ini_code",
        "Unnamed: 5":"est_ini",
        "Unnamed: 7":"est_fin_code",
        "Unnamed: 9":"est_fin",
        "Unnamed: 11":"tiempo_min",
        "Unnamed: 13":"peso"
    }
    tiempos = tiempos.rename(columns=col_map)[list(col_map.values())]
    tiempos = tiempos.dropna(subset=["linea","est_ini_code","est_fin_code"])
    tiempos["linea"] = pd.to_numeric(tiempos["linea"], errors="coerce")
    tiempos["tiempo_min"] = pd.to_numeric(tiempos["tiempo_min"], errors="coerce")
    tiempos["peso"] = pd.to_numeric(tiempos["peso"], errors="coerce")
    tiempos = tiempos.dropna(subset=["linea","tiempo_min"])
    tiempos["est_ini"] = tiempos["est_ini"].astype(str).str.strip()
    tiempos["est_fin"] = tiempos["est_fin"].astype(str).str.strip()

    # ---- limpiar TRANSBORDOS ----
    trans_map = {
        "Unnamed: 1":"linea_ini",
        "Unnamed: 2":"linea_fin",
        "Unnamed: 3":"est_tras_code",
        "Unnamed: 4":"tiempo_trans_min",
        "Unnamed: 7":"peso_trans"
    }
    trans = trans.rename(columns=trans_map)[list(trans_map.values())]
    trans = trans.dropna(subset=["linea_ini","linea_fin"])
    for c in ["linea_ini","linea_fin","tiempo_trans_min","peso_trans"]:
        trans[c] = pd.to_numeric(trans[c], errors="coerce")
    trans = trans.dropna(subset=["linea_ini","linea_fin","tiempo_trans_min"])

    # Mapear códigos -> nombres (desde TIEMPOS)
    code_to_name = {}
    for _, r in tiempos.iterrows():
        code_to_name.setdefault(str(r.est_ini_code).strip(), r.est_ini)
        code_to_name.setdefault(str(r.est_fin_code).strip(), r.est_fin)

    trans["est_tras"] = trans["est_tras_code"].astype(str).str.strip().map(code_to_name).fillna(trans["est_tras_code"])

    return tiempos, trans

# ---------- 3) CONSTRUIR GRAFO ----------
def construir_grafo(tiempos_df, trans_df):
    graph = defaultdict(list)   # graph[u] = [(v, linea, tiempo_min), ...]
    lines_at = defaultdict(set)

    # aristas por línea
    for _, r in tiempos_df.iterrows():
        u = r.est_ini.strip()
        v = r.est_fin.strip()
        l = int(r.linea)
        t = float(r.tiempo_min)

        graph[u].append((v, l, t))
        graph[v].append((u, l, t))
        lines_at[u].add(l)
        lines_at[v].add(l)

    # transferencias oficiales
    transfer = defaultdict(dict)
    for _, r in trans_df.iterrows():
        a = int(r.linea_ini)
        b = int(r.linea_fin)
        s = str(r.est_tras).strip()
        tt = float(r.tiempo_trans_min)
        # peso_trans no lo usamos para el costo base (solo si quieres penalizarlo aparte)
        transfer[s][(a,b)] = tt
        transfer[s][(b,a)] = tt

    return graph, lines_at, transfer

# ---------- 4) DIJKSTRA/A* MULTI-LÍNEA ----------
def ruta_optima(origen, destino, dt, graph, lines_at, transfer,
                dwell_min=TIEMPO_PARADA_MIN,
                usar_espera=USAR_ESPERA_PROMEDIO,
                alpha=ALPHA_PESO):
    """
    Encuentra ruta mínima considerando:
    - tiempos entre estaciones
    - tiempo de parada por estación
    - tiempos de transbordo oficiales
    - espera por frecuencia SOLO al subir a una línea nueva
    - pesos de frecuencia SOLO al subir a una línea nueva
    Devuelve: (path, (min_totales, peso_total))
    path = [(estacion, linea), ...]
    """
    if origen not in graph:
        raise ValueError(f"Origen '{origen}' no está en el grafo.")
    if destino not in graph:
        raise ValueError(f"Destino '{destino}' no está en el grafo.")

    tipo_dia = tipo_dia_desde_fecha(dt)
    hora = dt.time()

    # estados iniciales: elegir línea en origen (subida inicial)
    pq = []
    dist = {}       # dist[(est,line)] = (min, peso)
    prev = {}       # prev[(est,line)] = ((est_prev,line_prev), accion)

    for l in lines_at[origen]:
        freq, peso = frecuencia_y_peso(l, tipo_dia, hora)
        wait = freq/2.0 if usar_espera else freq
        st = (origen, l)
        dist[st] = (wait, peso)
        prev[st] = (None, f"start on line {l}")
        heapq.heappush(pq, (wait + alpha*peso, wait, peso, st))

    best_final = None
    best_cost = None

    while pq:
        f, gmin, gpeso, (u, line_u) = heapq.heappop(pq)
        if dist.get((u, line_u), (math.inf, math.inf)) != (gmin, gpeso):
            continue

        if u == destino:
            best_final = (u, line_u)
            best_cost = (gmin, gpeso)
            break

        # 4.1) mover a vecinos por la misma línea (sin pesos extra)
        for v, l_edge, t_edge in graph[u]:
            if l_edge != line_u:
                continue
            new_min = gmin + t_edge + dwell_min
            new_peso = gpeso
            st2 = (v, line_u)

            old_min, old_peso = dist.get(st2, (math.inf, math.inf))
            if new_min + alpha*new_peso < old_min + alpha*old_peso:
                dist[st2] = (new_min, new_peso)
                prev[st2] = ((u, line_u), f"ride line {line_u} to {v}")
                heapq.heappush(pq, (new_min + alpha*new_peso, new_min, new_peso, st2))

        # 4.2) transbordos oficiales en u (subes a línea nueva => sumas espera y peso)
        for l2 in lines_at[u]:
            if l2 == line_u:
                continue
            # solo si existe transbordo oficial
            if (line_u, l2) not in transfer.get(u, {}):
                continue

            t_trans = transfer[u][(line_u, l2)]

            freq2, peso2 = frecuencia_y_peso(l2, tipo_dia, hora)
            wait2 = freq2/2.0 if usar_espera else freq2

            new_min = gmin + t_trans + wait2
            new_peso = gpeso + peso2

            st2 = (u, l2)
            old_min, old_peso = dist.get(st2, (math.inf, math.inf))
            if new_min + alpha*new_peso < old_min + alpha*old_peso:
                dist[st2] = (new_min, new_peso)
                prev[st2] = ((u, line_u), f"transfer {line_u}->{l2} at {u}")
                heapq.heappush(pq, (new_min + alpha*new_peso, new_min, new_peso, st2))

    if best_final is None:
        return None

    # reconstrucción del path
    path = []
    st = best_final
    while st is not None:
        path.append(st)
        st, _act = prev[st]
    path.reverse()
    return path, best_cost

# ---------- 5) IMPRESIÓN AMIGABLE ----------
def describir_ruta(path):
    if not path:
        return "Sin ruta."
    out = []
    out.append(f"Inicio: {path[0][0]} (L{path[0][1]})")
    for i in range(1, len(path)):
        est, ln = path[i]
        est_prev, ln_prev = path[i-1]
        if ln != ln_prev:
            out.append(f"  Transbordo en {est_prev}: L{ln_prev} -> L{ln}")
        out.append(f"  -> {est} (L{ln})")
    out.append(f"Fin: {path[-1][0]} (L{path[-1][1]})")
    return "\n".join(out)

# ---------- 6) FUNCIÓN PRINCIPAL "MOOVIT-LIKE" ----------
def plan_viaje(origen, destino, fecha_hora=None):
    """
    origen, destino: nombres EXACTOS como en el Excel (con acentos).
    fecha_hora: datetime; si None usa ahora.
    """
    if fecha_hora is None:
        fecha_hora = datetime.now()

    tiempos_df, trans_df = cargar_datos_excel(FILE_PATH)
    graph, lines_at, transfer = construir_grafo(tiempos_df, trans_df)

    res = ruta_optima(origen, destino, fecha_hora, graph, lines_at, transfer)
    if res is None:
        print("No se encontró ruta.")
        return None

    path, (mins, peso_total) = res
    print(describir_ruta(path))
    print(f"\nTiempo total estimado: {mins:.1f} min")
    print(f"Peso total por frecuencias (solo al subir/cambiar línea): {peso_total:.0f}")
    print(f"Día tipo: {tipo_dia_desde_fecha(fecha_hora)}, hora: {fecha_hora.time()}")
    return path, mins, peso_total

# ---------- 7) EJEMPLO: TACUBAYA -> UNIVERSIDAD ----------
# Cambia fecha/hora a lo que quieras probar
if __name__ == "__main__":
    dt = datetime.strptime("2025-11-21 08:30", "%Y-%m-%d %H:%M")
    plan_viaje("Auditorio", "Balderas", dt)