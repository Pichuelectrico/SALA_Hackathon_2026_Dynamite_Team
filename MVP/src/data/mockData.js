// ============================================================
// DATOS MOCK — reemplazar con fetch() a backend/JSON real
// ============================================================

export const predictionData = {
  timestamp: new Date().toISOString(),
  willRain: true,
  probability: 0.82,           // 0–1
  intensity: "Moderada",       // "Ligera" | "Moderada" | "Intensa" | "Torrencial"
  intensityMmH: 4.3,           // mm/h esperados
  ci_lower: 2.1,               // límite inferior bootstrap 90%
  ci_upper: 7.8,               // límite superior bootstrap 90%
  ci_level: 0.90,
  horizon: 60,                 // minutos
  modelVersion: "RainSense v2.1 · Bootstrap n=500",
  nStations: 5,
};

export const stationsData = [
  {
    id: "CER",
    name: "Cerro Alto",
    lat: -0.82,
    lon: -89.45,
    status: "active",
    lastReading: 3.2,
    trend: "up",
    probability: 0.85,
    recentHours: [0.0, 0.4, 1.2, 3.2],
    file: "CER_consolid_f15.csv",
    description: "Highland station"
  },
  {
    id: "JUN",
    name: "El Junco",
    lat: -0.84,
    lon: -89.47,
    status: "active",
    lastReading: 5.1,
    trend: "up",
    probability: 0.91,
    recentHours: [0.2, 1.1, 2.8, 5.1],
    file: "JUN_consolid_f15.csv",
    description: "Near the freshwater lake at the island's summit"
  },
  {
    id: "MERC",
    name: "Merceditas",
    lat: -0.88,
    lon: -89.42,
    status: "active",
    lastReading: 1.7,
    trend: "stable",
    probability: 0.68,
    recentHours: [0.0, 0.0, 0.9, 1.7],
    file: "MERC_consolid_f15.csv",
    description: "Mid-elevation agricultural zone"
  },
  {
    id: "MIRA",
    name: "El Mirador",
    lat: -0.90,
    lon: -89.60,
    status: "active",
    lastReading: 0.3,
    trend: "down",
    probability: 0.41,
    recentHours: [1.4, 0.9, 0.5, 0.3],
    file: "MIRA_consolid_f15.csv",
    description: "Coastal/lowland station"
  }
];

// Serie temporal de las últimas 3 horas (datos combinados multiestación)
export const timeSeriesData = [
  { time: "-180 min", avg: 0.0, q10: 0.0, q90: 0.0 },
  { time: "-150 min", avg: 0.1, q10: 0.0, q90: 0.2 },
  { time: "-120 min", avg: 0.2, q10: 0.0, q90: 0.5 },
  { time: "-90 min",  avg: 0.5, q10: 0.1, q90: 1.1 },
  { time: "-60 min",  avg: 1.4, q10: 0.7, q90: 2.3 },
  { time: "-30 min",  avg: 2.8, q10: 1.5, q90: 4.2 },
  { time: "Ahora",    avg: 3.8, q10: 2.1, q90: 5.6 },
  { time: "+30 min",  avg: 4.3, q10: 2.1, q90: 7.8, forecast: true },
  { time: "+60 min",  avg: 3.5, q10: 1.4, q90: 6.9, forecast: true },
];

// Distribución bootstrap para el histograma
export const bootstrapDistribution = [
  { bin: "0–1",   count: 8 },
  { bin: "1–2",   count: 22 },
  { bin: "2–3",   count: 55 },
  { bin: "3–4",   count: 89 },
  { bin: "4–5",   count: 112 },
  { bin: "5–6",   count: 98 },
  { bin: "6–7",   count: 67 },
  { bin: "7–8",   count: 33 },
  { bin: "8–9",   count: 12 },
  { bin: "9–10",  count: 4 },
];

export const alertLevels = {
  current: "medio",   // "bajo" | "medio" | "alto"
  thresholds: {
    bajo: { max: 2, label: "Lluvia ligera prevista", color: "sky" },
    medio: { max: 5, label: "Lluvia moderada prevista", color: "amber" },
    alto: { max: Infinity, label: "Lluvia intensa prevista", color: "red" },
  },
  messages: [
    { level: "medio", text: "Probabilidad alta de lluvia en la próxima hora." },
    { level: "medio", text: "Se recomienda llevar paraguas si sale al exterior." },
    { level: "bajo",  text: "Estación EST-04 (Cumbayá) muestra tendencia decreciente." },
  ],
};
