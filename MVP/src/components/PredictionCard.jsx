import { Droplets, TrendingUp, ShieldCheck, AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";

function ProbabilityRing({ probability }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const [offset, setOffset] = useState(circ);

  useEffect(() => {
    const timer = setTimeout(() => {
      setOffset(circ * (1 - probability));
    }, 300);
    return () => clearTimeout(timer);
  }, [probability, circ]);

  const color =
    probability >= 0.7 ? "#3b82f6" : probability >= 0.4 ? "#f59e0b" : "#94a3b8";

  return (
    <svg width="140" height="140" viewBox="0 0 140 140" className="drop-shadow-lg">
      {/* Track */}
      <circle
        cx="70" cy="70" r={r}
        fill="none"
        stroke="rgba(255,255,255,0.07)"
        strokeWidth="10"
      />
      {/* Progress */}
      <circle
        cx="70" cy="70" r={r}
        fill="none"
        stroke={color}
        strokeWidth="10"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{
          transform: "rotate(-90deg)",
          transformOrigin: "70px 70px",
          transition: "stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)",
          filter: `drop-shadow(0 0 8px ${color}88)`,
        }}
      />
      {/* Value */}
      <text
        x="70" y="65"
        textAnchor="middle"
        fill="white"
        fontSize="26"
        fontWeight="700"
        fontFamily="DM Sans, sans-serif"
      >
        {Math.round(probability * 100)}%
      </text>
      <text
        x="70" y="83"
        textAnchor="middle"
        fill="#94a3b8"
        fontSize="10"
        fontFamily="DM Sans, sans-serif"
        letterSpacing="1"
      >
        PROB.
      </text>
    </svg>
  );
}

function RainDrops({ active }) {
  if (!active) return null;
  const drops = Array.from({ length: 8 }, (_, i) => ({
    left: `${10 + i * 11}%`,
    height: `${12 + Math.random() * 14}px`,
    delay: `${i * 0.18}s`,
    duration: `${0.9 + Math.random() * 0.6}s`,
    opacity: 0.3 + Math.random() * 0.5,
  }));

  return (
    <div className="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">
      {drops.map((d, i) => (
        <div
          key={i}
          className="absolute bottom-0 w-0.5 rounded-full bg-gradient-to-b from-transparent to-blue-300"
          style={{
            left: d.left,
            height: d.height,
            opacity: d.opacity,
            animation: `fall ${d.duration} ${d.delay} linear infinite`,
          }}
        />
      ))}
    </div>
  );
}

const intensityConfig = {
  Ligera:      { color: "text-sky-300",  bg: "bg-sky-500/10",   border: "border-sky-400/30"  },
  Moderada:    { color: "text-blue-300", bg: "bg-blue-500/10",  border: "border-blue-400/30" },
  Intensa:     { color: "text-indigo-300", bg: "bg-indigo-500/10", border: "border-indigo-400/30" },
  Torrencial:  { color: "text-purple-300", bg: "bg-purple-500/10", border: "border-purple-400/30" },
};

export default function PredictionCard({ data }) {
  const { willRain, probability, intensity, intensityMmH, ci_lower, ci_upper, ci_level } = data;
  const cfg = intensityConfig[intensity] || intensityConfig["Moderada"];
  const ciPct = Math.round(ci_level * 100);

  return (
    <div className="relative card-glow overflow-hidden p-6 lg:p-8 animate-count-up">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/30 via-slate-900/20 to-cyan-900/10 pointer-events-none" />
      <RainDrops active={willRain} />

      <div className="relative z-10 flex flex-col lg:flex-row gap-8 items-center lg:items-start">

        {/* Probability Ring */}
        <div className="flex flex-col items-center gap-3 flex-shrink-0">
          <ProbabilityRing probability={probability} />
          <div className={`badge ${willRain ? "bg-blue-500/20 border border-blue-400/30 text-blue-200" : "bg-slate-500/20 border border-slate-400/30 text-slate-300"}`}>
            {willRain ? (
              <><Droplets className="w-3 h-3" /> Lluvia prevista</>
            ) : (
              <><ShieldCheck className="w-3 h-3" /> Sin lluvia</>
            )}
          </div>
        </div>

        {/* Stats grid */}
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-5 w-full">

          {/* ¿Va a llover? */}
          <div className="col-span-1 sm:col-span-3 flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full animate-pulse ${willRain ? "bg-blue-400" : "bg-slate-500"}`} />
            <h2 className="text-xl lg:text-2xl font-semibold text-white">
              {willRain ? "Se espera lluvia en la próxima hora" : "No se espera lluvia en la próxima hora"}
            </h2>
          </div>

          {/* Intensidad */}
          <div className={`rounded-xl p-4 border ${cfg.bg} ${cfg.border}`}>
            <p className="stat-label mb-2 flex items-center gap-1.5">
              <Droplets className="w-3.5 h-3.5" />
              Intensidad
            </p>
            <p className={`text-2xl font-bold ${cfg.color}`}>{intensity}</p>
            <p className="font-mono text-sm mt-1 text-slate-400">
              {intensityMmH.toFixed(1)} <span className="text-xs">mm/h</span>
            </p>
          </div>

          {/* Intervalo de confianza */}
          <div className="rounded-xl p-4 border bg-white/5 border-white/10">
            <p className="stat-label mb-2 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              IC {ciPct}%
            </p>
            <p className="text-2xl font-bold text-white">
              {ci_lower.toFixed(1)}–{ci_upper.toFixed(1)}
            </p>
            <p className="font-mono text-sm mt-1 text-slate-400">mm/h</p>
          </div>

          {/* Tendencia */}
          <div className="rounded-xl p-4 border bg-emerald-500/5 border-emerald-400/20">
            <p className="stat-label mb-2 flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5" />
              Tendencia
            </p>
            <p className="text-2xl font-bold text-emerald-300">↑ Subiendo</p>
            <p className="text-sm mt-1 text-slate-400">últ. 3 horas</p>
          </div>

        </div>
      </div>

      {/* Confidence bar */}
      <div className="relative z-10 mt-6 pt-5 border-t border-white/10">
        <div className="flex justify-between items-center mb-2">
          <span className="stat-label">Confianza del modelo</span>
          <span className="font-mono text-xs text-blue-300">{Math.round(probability * 100)}% certeza</span>
        </div>
        <div className="h-2 rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400"
            style={{
              width: `${probability * 100}%`,
              transition: "width 1.5s cubic-bezier(0.4,0,0.2,1)",
              boxShadow: "0 0 12px rgba(59,130,246,0.6)",
            }}
          />
        </div>
        <div className="flex justify-between mt-1 text-xs text-slate-600 font-mono">
          <span>0%</span><span>50%</span><span>100%</span>
        </div>
      </div>
    </div>
  );
}
