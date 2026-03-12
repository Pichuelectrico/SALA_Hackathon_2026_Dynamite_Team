import { Cpu, Database, GitBranch, Clock } from "lucide-react";

export default function ModelSummary({ data }) {
  const items = [
    {
      icon: <Cpu className="w-4 h-4 text-blue-400" />,
      label: "Modelo",
      value: "RainSense v2.1",
    },
    {
      icon: <Database className="w-4 h-4 text-blue-400" />,
      label: "Muestras Bootstrap",
      value: "n = 500",
    },
    {
      icon: <GitBranch className="w-4 h-4 text-blue-400" />,
      label: "Estaciones",
      value: `${data.nStations} activas`,
    },
    {
      icon: <Clock className="w-4 h-4 text-blue-400" />,
      label: "Horizonte",
      value: `${data.horizon} min`,
    },
  ];

  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-4">
        <Cpu className="w-4 h-4 text-blue-400" />
        <h3 className="font-semibold text-white text-sm uppercase tracking-wider">
          Resumen Técnico
        </h3>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {items.map((item) => (
          <div key={item.label} className="rounded-lg bg-white/5 p-3">
            <div className="flex items-center gap-1.5 mb-1">
              {item.icon}
              <span className="text-xs text-slate-500 uppercase tracking-wider">{item.label}</span>
            </div>
            <p className="font-mono text-sm font-medium text-white">{item.value}</p>
          </div>
        ))}
      </div>

      <p className="text-xs text-slate-600 mt-3 font-mono">
        {data.modelVersion} · IC calculado sobre precipitación media multiestación de las últimas 3h.
      </p>
    </div>
  );
}
