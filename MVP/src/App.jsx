import { useState, useCallback } from "react";
import Header from "./components/Header";
import PredictionCard from "./components/PredictionCard";
import StationsPanel from "./components/StationsPanel";
import TimeSeriesChart from "./components/TimeSeriesChart";
import UncertaintyPanel from "./components/UncertaintyPanel";
import AlertPanel from "./components/AlertPanel";
import ModelSummary from "./components/ModelSummary";
import { horizonsData } from "./data/mockData";

const HORIZONS = [
  { key: "h1", label: "1 hora",  short: "1h", desc: "Mayor precisión" },
  { key: "h3", label: "3 horas", short: "3h", desc: "Medio plazo" },
  { key: "h6", label: "6 horas", short: "6h", desc: "Largo plazo" },
];

export default function App() {
  const [activeHorizon, setActiveHorizon] = useState("h1");
  const data = horizonsData[activeHorizon];

  return (
    <div className="min-h-screen noise-bg relative">
      {/* Background blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-blue-900/20 blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full bg-cyan-900/15 blur-[100px] animate-pulse-slow" style={{ animationDelay: "1.5s" }} />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

        <Header timestamp={data.prediction.timestamp} />

        {/* Selector de horizonte */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 uppercase tracking-widest mr-2">Horizonte de predicción</span>
          {HORIZONS.map((h) => (
            <button
              key={h.key}
              onClick={() => setActiveHorizon(h.key)}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all duration-200 border
                ${activeHorizon === h.key
                  ? "bg-blue-500/20 border-blue-400/50 text-blue-200 shadow-lg shadow-blue-900/30"
                  : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-slate-200"
                }`}
            >
              <span className="font-mono font-bold">{h.short}</span>
              <span className="text-xs opacity-70 hidden sm:inline">{h.desc}</span>
            </button>
          ))}
        </div>

        {/* Hero */}
        <PredictionCard data={data.prediction} />

        {/* Chart + Alert */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TimeSeriesChart data={data.timeSeries} />
          </div>
          <div>
            <AlertPanel alertData={data.alerts} />
          </div>
        </div>

        {/* Stations */}
        <StationsPanel stations={data.stations} />

        {/* Bootstrap */}
        <UncertaintyPanel
          distribution={data.bootstrap}
          ciLower={data.prediction.ci_lower}
          ciUpper={data.prediction.ci_upper}
          mean={data.prediction.intensityMmH || data.prediction.probability}
        />

        {/* Model summary */}
        <ModelSummary data={data.prediction} metrics={data.metrics} />

        <footer className="text-center text-xs text-slate-700 pb-4 font-mono">
          RainSense · Sistema Probabilístico Multiestación · Quito, Ecuador
        </footer>
      </div>
    </div>
  );
}
