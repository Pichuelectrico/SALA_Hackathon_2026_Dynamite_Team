import { Radio, TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";

function TrendIcon({ trend }) {
  if (trend === "up")     return <TrendingUp className="w-4 h-4 text-blue-400" />;
  if (trend === "down")   return <TrendingDown className="w-4 h-4 text-slate-400" />;
  return <Minus className="w-4 h-4 text-slate-500" />;
}

function MiniSparkline({ values }) {
  const max = Math.max(...values, 0.1);
  const w = 80, h = 28;
  const step = w / (values.length - 1);
  const pts = values
    .map((v, i) => `${i * step},${h - (v / max) * (h - 2) - 1}`)
    .join(" ");
  const area = `${pts} ${(values.length - 1) * step},${h} 0,${h}`;

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="overflow-visible">
      <defs>
        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={area} fill="url(#sparkGrad)" />
      <polyline
        points={pts}
        fill="none"
        stroke="#60a5fa"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* last point dot */}
      <circle
        cx={(values.length - 1) * step}
        cy={h - (values[values.length - 1] / max) * (h - 2) - 1}
        r="2.5"
        fill="#93c5fd"
      />
    </svg>
  );
}

function StationCard({ station }) {
  const probPct = Math.round(station.probability * 100);
  const isWarning = station.status === "warning";

  return (
    <div className={`card p-4 transition-all duration-200 hover:border-blue-400/30 hover:bg-white/[0.07]
      ${isWarning ? "border-amber-400/20" : ""}`}>
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
              isWarning ? "bg-amber-400 animate-pulse" : "bg-emerald-400"
            }`} />
            <span className="text-sm font-semibold text-white">{station.name}</span>
            {isWarning && <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />}
          </div>
          <span className="font-mono text-xs text-slate-500 pl-4">{station.id}</span>
        </div>
        <TrendIcon trend={station.trend} />
      </div>

      {/* Sparkline */}
      <div className="mb-3">
        <MiniSparkline values={station.recentHours} />
      </div>

      {/* Stats row */}
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider">Actual</p>
          <p className="font-mono text-lg font-bold text-white">
            {station.lastReading.toFixed(1)}
            <span className="text-xs text-slate-400 ml-1">mm/h</span>
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500 uppercase tracking-wider">P(lluvia)</p>
          <div className="flex items-center gap-1.5 justify-end">
            <div className="w-14 h-1.5 rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-blue-400"
                style={{ width: `${probPct}%` }}
              />
            </div>
            <span className="font-mono text-sm text-blue-300">{probPct}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function StationsPanel({ stations }) {
  return (
    <div className="card-glow p-5">
      <div className="flex items-center gap-2 mb-4">
        <Radio className="w-4 h-4 text-blue-400" />
        <h3 className="font-semibold text-white text-sm uppercase tracking-wider">
          Estaciones Meteorológicas
        </h3>
        <span className="ml-auto badge bg-emerald-500/10 border border-emerald-400/20 text-emerald-300">
          {stations.filter(s => s.status === "active").length}/{stations.length} activas
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
        {stations.map((station) => (
          <StationCard key={station.id} station={station} />
        ))}
      </div>
    </div>
  );
}
