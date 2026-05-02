from flask import Flask, jsonify, request
from datetime import datetime
from dateutil import tz
import metro_algo as algo  # <-- coloca tu código en metro_algo.py

app = Flask(__name__, static_url_path="", static_folder="static")

# Cargar datos desde el Excel configurado en metro_algo.FILE_PATH
tiempos_df, trans_df = algo.cargar_datos_excel(algo.FILE_PATH)
graph, lines_at, transfer = algo.construir_grafo(tiempos_df, trans_df)
STATIONS = sorted(graph.keys())

@app.get("/")
def root():
    return app.send_static_file("index.html")

@app.get("/api/stations")
def stations():
    return jsonify({"stations": STATIONS})

@app.post("/api/route")
def route():
    data = request.get_json(force=True)
    origin = data.get("from")
    dest   = data.get("to")
    now_cdmx = datetime.now(tz.gettz("America/Mexico_City"))
    res = algo.ruta_optima(origin, dest, now_cdmx, graph, lines_at, transfer)
    if res is None:
        return jsonify({"path": None, "error":"No se encontró ruta"}), 200
    path, (mins, peso_total) = res
    stations = [p[0] for p in path]
    lines_seq = [p[1] for p in path]
    transfers = 0
    used_lines = []
    prev = None
    for l in lines_seq:
        if prev is None:
            used_lines.append(l)
        elif l != prev:
            transfers += 1
            used_lines.append(l)
        prev = l
    steps = []
    for i in range(len(path)-1):
        u, lu = path[i]; v, lv = path[i+1]
        action = "transfer" if lu != lv else "ride"
        steps.append({"from": u, "to": v, "line_from": lu, "line_to": lv, "action": action})
    return jsonify({
        "summary": {"from": origin, "to": dest, "time_min": round(mins,1),
                    "transfers": transfers, "lines": used_lines,
                    "datetime_local": now_cdmx.isoformat()},
        "path": stations, "steps": steps
    })

if __name__ == "__main__":
    app.run(debug=True)
