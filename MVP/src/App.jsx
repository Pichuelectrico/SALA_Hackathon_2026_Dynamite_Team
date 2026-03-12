import { useState, useCallback } from "react";
import Header from "./components/Header";
import PredictionCard from "./components/PredictionCard";
import StationsPanel from "./components/StationsPanel";
import TimeSeriesChart from "./components/TimeSeriesChart";
import UncertaintyPanel from "./components/UncertaintyPanel";
import AlertPanel from "./components/AlertPanel";
import ModelSummary from "./components/ModelSummary";

import {
  predictionData,
  stationsData,
  timeSeriesData,
  bootstrapDistribution,
  alertLevels,
} from "./data/mockData";

// ─────────────────────────────────────────────────────────────
// Para conectar con backend real, reemplaza loadData() con:
//   const res = await fetch("/api/prediction");
//   const json = await res.json();
//   return json;
// ─────────────────────────────────────────────────────────────
function loadData() {
  return {
    prediction: { ...predictionData, timestamp: new Date().toISOString() },
    stations: stationsData,
    timeSeries: timeSeriesData,
    bootstrap: bootstrapDistribution,
    alerts: alertLevels,
  };
}

export default function App() {
  const [data, setData] = useState(loadData);

  const handleRefresh = useCallback(() => {
    setData(loadData());
  }, []);

  return (
    <div className="min-h-screen noise-bg relative">
      {/* Atmospheric background blobs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full
          bg-blue-900/20 blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-[-10%] right-[-5%] w-[500px] h-[500px] rounded-full
          bg-cyan-900/15 blur-[100px] animate-pulse-slow" style={{ animationDelay: "1.5s" }} />
        <div className="absolute top-[40%] left-[30%] w-[300px] h-[300px] rounded-full
          bg-blue-800/10 blur-[80px]" />
      </div>

      {/* Main layout */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

        <Header
          timestamp={data.prediction.timestamp}
          onRefresh={handleRefresh}
        />

        {/* Hero prediction card */}
        <section>
          <PredictionCard data={data.prediction} />
        </section>

        {/* Two-column: chart + alert */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TimeSeriesChart data={data.timeSeries} />
          </div>
          <div>
            <AlertPanel alertData={data.alerts} />
          </div>
        </section>

        {/* Stations */}
        <section>
          <StationsPanel stations={data.stations} />
        </section>

        {/* Bootstrap uncertainty */}
        <section>
          <UncertaintyPanel
            distribution={data.bootstrap}
            ciLower={data.prediction.ci_lower}
            ciUpper={data.prediction.ci_upper}
            mean={data.prediction.intensityMmH}
          />
        </section>

        {/* Model summary */}
        <section>
          <ModelSummary data={data.prediction} />
        </section>

        <footer className="text-center text-xs text-slate-700 pb-4 font-mono">
          RainSense · Sistema Probabilístico Multiestación · Quito, Ecuador
        </footer>
      </div>
    </div>
  );
}
