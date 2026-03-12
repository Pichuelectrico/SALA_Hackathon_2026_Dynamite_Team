import { CloudRain, RefreshCw, Radio, Cpu } from "lucide-react";

export default function Header({ timestamp, onRefresh }) {
  const formatted = new Date(timestamp).toLocaleString("es-EC", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <header className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-white/10">
      {/* Logo + título */}
      <div className="flex items-center gap-4">
        <div className="relative flex items-center justify-center w-12 h-12 rounded-xl bg-blue-500/20 border border-blue-400/30 glow-blue">
          <CloudRain className="w-6 h-6 text-blue-300" strokeWidth={1.5} />
          {/* live indicator */}
          <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-400 border-2 border-[#050d1a] animate-pulse" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Rain<span className="text-blue-400">Sense</span>
          </h1>
          <p className="text-xs text-slate-400 tracking-wide">
            Sistema Probabilístico de Alerta Temprana · Quito, Ecuador
          </p>
        </div>
      </div>

      {/* Meta info */}
      <div className="flex items-center gap-3 sm:gap-5 flex-wrap">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span>5 estaciones activas</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-mono">Bootstrap n=500</span>
        </div>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium
            bg-blue-500/10 border border-blue-400/20 text-blue-300
            hover:bg-blue-500/20 hover:border-blue-400/40 transition-all duration-200"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {formatted}
        </button>
      </div>
    </header>
  );
}
