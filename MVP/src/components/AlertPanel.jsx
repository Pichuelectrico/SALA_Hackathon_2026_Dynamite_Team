import { Bell, Info, AlertTriangle, AlertOctagon, CheckCircle } from "lucide-react";

const levelConfig = {
  bajo: {
    label: "ALERTA BAJA",
    icon: Info,
    color: "text-sky-300",
    bg: "bg-sky-500/10",
    border: "border-sky-400/30",
    ring: "ring-sky-400/20",
    dot: "bg-sky-400",
    description: "Probabilidad baja. Condiciones estables.",
  },
  medio: {
    label: "ALERTA MEDIA",
    icon: AlertTriangle,
    color: "text-amber-300",
    bg: "bg-amber-500/10",
    border: "border-amber-400/30",
    ring: "ring-amber-400/20",
    dot: "bg-amber-400",
    description: "Probabilidad moderada/alta. Tomar precauciones.",
  },
  alto: {
    label: "ALERTA ALTA",
    icon: AlertOctagon,
    color: "text-red-300",
    bg: "bg-red-500/10",
    border: "border-red-400/30",
    ring: "ring-red-400/20",
    dot: "bg-red-400",
    description: "Lluvia intensa inminente. Acción inmediata.",
  },
};

const msgLevelDot = {
  bajo:  "bg-sky-400",
  medio: "bg-amber-400",
  alto:  "bg-red-400",
};

export default function AlertPanel({ alertData }) {
  const { current, messages } = alertData;
  const cfg = levelConfig[current];
  const Icon = cfg.icon;

  return (
    <div className="card-glow p-5">
      <div className="flex items-center gap-2 mb-4">
        <Bell className="w-4 h-4 text-blue-400" />
        <h3 className="font-semibold text-white text-sm uppercase tracking-wider">
          Panel de Alertas
        </h3>
      </div>

      {/* Active alert badge */}
      <div className={`flex items-center gap-3 rounded-xl p-4 border mb-4 ${cfg.bg} ${cfg.border}`}>
        <div className={`flex items-center justify-center w-10 h-10 rounded-full ${cfg.bg} ring-2 ${cfg.ring} flex-shrink-0`}>
          <Icon className={`w-5 h-5 ${cfg.color}`} />
        </div>
        <div>
          <p className={`font-bold text-sm tracking-wider ${cfg.color}`}>{cfg.label}</p>
          <p className="text-xs text-slate-400 mt-0.5">{cfg.description}</p>
        </div>
        <span className={`ml-auto w-3 h-3 rounded-full flex-shrink-0 ${cfg.dot} animate-pulse`} />
      </div>

      {/* Level scale */}
      <div className="flex rounded-lg overflow-hidden mb-4 h-2">
        {["bajo", "medio", "alto"].map((lvl) => (
          <div
            key={lvl}
            className={`flex-1 transition-opacity duration-300 ${
              lvl === "bajo" ? "bg-sky-500" : lvl === "medio" ? "bg-amber-500" : "bg-red-500"
            } ${current === lvl ? "opacity-100" : "opacity-20"}`}
          />
        ))}
      </div>
      <div className="flex justify-between text-xs text-slate-600 font-mono mb-4">
        <span>BAJO</span><span>MEDIO</span><span>ALTO</span>
      </div>

      {/* Messages */}
      <div className="space-y-2">
        {messages.map((msg, i) => (
          <div key={i} className="flex items-start gap-2.5 text-xs text-slate-300">
            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1 ${msgLevelDot[msg.level]}`} />
            {msg.text}
          </div>
        ))}
      </div>
    </div>
  );
}
