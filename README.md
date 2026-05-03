# 🚇 Metro CDMX Router

Proyecto de Inteligencia Artificial centrado en el cálculo de rutas dentro de la red del Metro de Ciudad de México, intentando aproximar el comportamiento real del sistema más allá de un simple camino mínimo.

---

## 🧩 Descripción

El objetivo del proyecto es encontrar la mejor ruta entre dos estaciones del metro, teniendo en cuenta no solo la distancia, sino también factores que influyen en la experiencia real del usuario.

Para ello, se ha construido un modelo basado en grafos donde se integran:

* Tiempos entre estaciones
* Tiempo de parada en cada estación
* Coste de los transbordos
* Frecuencia de paso de los trenes
* Variaciones según la hora del día y el tipo de día

Esto permite obtener rutas que no solo son cortas, sino también realistas en términos de tiempo total.

---

## 🧠 Modelado del problema

La red se representa como un **grafo ponderado**, donde:

* Cada nodo es una estación
* Cada arista representa una conexión entre estaciones
* Los pesos reflejan tiempos reales de desplazamiento

Uno de los puntos clave del trabajo ha sido el tratamiento de los transbordos. En estaciones con múltiples líneas, como Tacubaya, se ha optado por modelar cada combinación de líneas como nodos distintos. Esto permite asignar distintos costes dependiendo del tipo de transbordo, evitando simplificaciones que distorsionarían el resultado.

Además, se ha incorporado el tiempo de espera medio en función de la frecuencia de cada línea, lo que introduce un componente dinámico en el cálculo de rutas.

---

## ⚙️ Algoritmo

Para el cálculo de rutas se ha utilizado el algoritmo A*, que permite encontrar soluciones óptimas combinando:

* El coste acumulado del recorrido
* Una estimación del coste restante

Este enfoque resulta especialmente útil en este problema, ya que permite trabajar con un grafo relativamente complejo sin perder eficiencia.

---

## 🖥️ Interfaz

Se ha desarrollado una interfaz web sencilla utilizando Flask y HTML, inspirada en herramientas como Google Maps.

El usuario puede:

* Seleccionar estación de origen y destino
* Calcular la ruta óptima
* Visualizar el recorrido sobre el mapa
* Consultar el listado de estaciones del trayecto

También se incluyen opciones para intercambiar estaciones y reiniciar la búsqueda.

---

## 📁 Estructura del proyecto

```
metro-cdmx-router/
│
├── server.py
├── metro_algo.py
├── requirements.txt
│
├── data/
│   └── IA - TIEMPOS TRASLADOS.xlsx
│
├── static/
│   └── index.html
│
└── docs/
    └── MEMORIA IA.pdf
```

---

## 🚀 Ejecución

1. Clonar el repositorio:

```bash
git clone https://github.com/pabloogarciia/metro-cdmx-router.git
cd metro-cdmx-router
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar el servidor:

```bash
python server.py
```

4. Abrir en el navegador:

```
http://127.0.0.1:5000
```

---

## ⚠️ Consideraciones

* El archivo Excel contiene los datos necesarios para el funcionamiento del sistema
* Las rutas deben ser relativas dentro del proyecto
* La hora del sistema influye en el cálculo de rutas

---

## 📌 Aspectos destacables

* Modelado detallado de transbordos
* Integración de frecuencias reales
* Adaptación del algoritmo A* a un problema con múltiples variables
* Separación clara entre lógica y visualización

---

## 👥 Autores

* Celia González Ortiz
* Javier García Hernández
* Claudia Lastra Díaz
* Pablo García Arroyo
* Alberto Font Zornoza

---

## 📝 Notas finales

Este proyecto no se ha centrado únicamente en implementar un algoritmo de búsqueda, sino en adaptarlo a un contexto más realista, donde intervienen múltiples factores que afectan al tiempo total de un trayecto.

El principal reto ha sido encontrar un equilibrio entre precisión del modelo y complejidad de implementación.
