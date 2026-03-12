import { Cpu, Database, GitBranch, Clock, BarChart2 } from "lucide-react";

function MetricBar({ value, color = "bg-blue-500" }) {
  return (
    <div className="h-1.5 rounded-full bg-white/10 overflow-hidden mt-1.5">
      <div className={`h-full rounded-full ${color}`}
        style={{ width: `${value * 100}%`, transition: "width 1s ease" }} />
    </div>
  );
}

export default function ModelSummary({ data, metrics }) {
  const infoItems = [
    { icon: <Cpu className="w-4 h-4 text-blue-400" />,       label: "Modelo",        value: metrics.best_model },
    { icon: <Clock className="w-4 h-4 text-blue-400" />,     label: "Horizonte",     value: data.horizonLabel },
    { icon: <GitBranch className="w-4 h-4 text-blue-400" />, label: "Estaciones",    value: `${data.nStations} activas` },
    { icon: <Database className="w-4 h-4 text-blue-400" />,  label: "Filas de test", value: metrics.test_rows.toLocaleString() },
  ];
  const metricItems = [
    { label: "Accuracy",        value: metrics.accuracy,    color: "bg-blue-500" },
    { label: "F1 Weighted",     value: metrics.f1_weighted, color: "bg-cyan-500" },
    { label: "F1 Macro",        value: metrics.f1_macro,    color: "bg-sky-400"  },
  ];
  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-4">
        <BarChart2 className="w-4 h-4 text-blue-400" />
        <h3 className="font-semibold text-white text-sm uppercase tracking-wider">Resumen Técnico del Modelo</h3>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        {infoItems.map((item) => (
          <div key={item.label} className="rounded-lg bg-white/5 p-3">
            <div className="flex items-center gap-1.5 mb-1">{item.icon}
              <span className="text-xs text-slate-500 uppercase tracking-wider">{item.label}</span>
            </div>
            <p className="font-mono text-sm font-medium text-white">{item.value}</p>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {metricItems.map((item) => (
          <div key={item.label}>
            <div className="flex justify-between items-center">
              <span className="text-xs text-slate-500 uppercase tracking-wider">{item.label}</span>
              <span className="font-mono text-xs text-white font-medium">{(item.value * 100).toFixed(1)}%</span>
            </div>
            <MetricBar value={item.value} color={item.color} />
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-600 mt-4 font-mono">
        {data.modelVersion} · Clases: 0=Sin lluvia · 1=Ligera · 2=Moderada/Intensa
      </p>
    </div>
  );
}
