# 🌧️ RainSense — Sistema Probabilístico de Alerta Temprana

Dashboard web interactivo para un sistema multiestación de predicción de precipitación con cuantificación de incertidumbre mediante bootstrap.

## 🚀 Instalación y ejecución

```bash
# 1. Instalar dependencias
npm install

# 2. Iniciar servidor de desarrollo
npm run dev

# 3. Abrir en el navegador
# → http://localhost:5173
```

## 🏗️ Estructura del proyecto

```
src/
├── components/
│   ├── Header.jsx           # Encabezado con estado de red y hora
│   ├── PredictionCard.jsx   # Card principal: prob., intensidad, IC
│   ├── StationsPanel.jsx    # Grid de tarjetas de estaciones
│   ├── TimeSeriesChart.jsx  # Gráfica temporal con pronóstico
│   ├── UncertaintyPanel.jsx # Histograma bootstrap + IC
│   ├── AlertPanel.jsx       # Semáforo de alertas
│   └── ModelSummary.jsx     # Parámetros técnicos del modelo
├── data/
│   └── mockData.js          # ← Reemplazar con fetch() real
├── App.jsx                  # Layout principal + estado global
├── main.jsx                 # Entry point
└── index.css                # Estilos Tailwind + animaciones
```

## 🔌 Conectar con backend real

En `src/App.jsx`, reemplaza la función `loadData()`:

```js
// Desde API REST
async function loadData() {
  const res = await fetch("/api/prediction");
  return await res.json();
}

// Desde archivo JSON
async function loadData() {
  const res = await fetch("/data/latest.json");
  return await res.json();
}
```

El JSON esperado tiene esta forma:

```json
{
  "prediction": {
    "timestamp": "ISO string",
    "willRain": true,
    "probability": 0.82,
    "intensity": "Moderada",
    "intensityMmH": 4.3,
    "ci_lower": 2.1,
    "ci_upper": 7.8,
    "ci_level": 0.90,
    "horizon": 60,
    "nStations": 5,
    "modelVersion": "RainSense v2.1"
  },
  "stations": [...],
  "timeSeries": [...],
  "bootstrap": [...],
  "alerts": { "current": "medio", "messages": [...] }
}
```

## 🎨 Stack

| Herramienta | Uso |
|-------------|-----|
| React 18    | UI  |
| Vite 5      | Bundler |
| Tailwind CSS 3 | Estilos |
| Recharts    | Gráficas |
| Lucide React | Íconos |

## 📦 Build para producción

```bash
npm run build   # genera /dist/
npm run preview # previsualiza el build
```
