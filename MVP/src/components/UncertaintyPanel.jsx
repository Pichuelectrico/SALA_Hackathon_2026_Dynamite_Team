import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Cell
} from "recharts";
import { Activity } from "lucide-react";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-blue-400/20 bg-slate-900/95 p-3 text-xs shadow-xl">
      <p className="font-semibold text-white">{label} mm/h</p>
      <p className="text-slate-300 font-mono mt-1">{payload[0].value} muestras bootstrap</p>
    </div>
  );
};

export default function UncertaintyPanel({ distribution, ciLower, ciUpper, mean }) {
  // Determinar si cada bin está dentro del IC
  const parseBin = (bin) => {
    const [lo] = bin.split("–").map(Number);
    return lo;
  };

  return (
    <div className="card-glow p-5">
      <div className="flex items-center gap-2 mb-2">
        <Activity className="w-4 h-4 text-blue-400" />
        <h3 className="font-semibold text-white text-sm uppercase tracking-wider">
          Distribución Bootstrap
        </h3>
        <span className="ml-auto font-mono text-xs text-slate-500">n = 500</span>
      </div>

      <p className="text-xs text-slate-500 mb-4">
        Distribución empírica de la intensidad estimada mediante remuestreo bootstrap.
        El área sombreada representa el intervalo de confianza del 90%.
      </p>

      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={distribution} margin={{ top: 5, right: 10, left: -20, bottom: 0 }} barCategoryGap="10%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis
            dataKey="bin"
            tick={{ fill: "#64748b", fontSize: 10, fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 10, fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* IC lower bound */}
          <ReferenceLine
            x={`${Math.floor(ciLower)}–${Math.floor(ciLower) + 1}`}
            stroke="rgba(251,191,36,0.5)"
            strokeDasharray="4 3"
          />
          {/* IC upper bound */}
          <ReferenceLine
            x={`${Math.floor(ciUpper)}–${Math.floor(ciUpper) + 1}`}
            stroke="rgba(251,191,36,0.5)"
            strokeDasharray="4 3"
          />
          {/* Mean */}
          <ReferenceLine
            x={`${Math.floor(mean)}–${Math.floor(mean) + 1}`}
            stroke="rgba(96,165,250,0.8)"
            strokeWidth={2}
          />

          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {distribution.map((entry) => {
              const lo = parseBin(entry.bin);
              const inCI = lo >= Math.floor(ciLower) && lo <= Math.ceil(ciUpper);
              return (
                <Cell
                  key={entry.bin}
                  fill={inCI ? "#3b82f6" : "#1e3a5f"}
                  fillOpacity={inCI ? 0.8 : 0.5}
                />
              );
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* IC summary */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        {[
          { label: "Límite inferior IC 90%", val: `${ciLower.toFixed(1)} mm/h`, color: "text-amber-300" },
          { label: "Media bootstrap",         val: `${mean.toFixed(1)} mm/h`,   color: "text-blue-300" },
          { label: "Límite superior IC 90%",  val: `${ciUpper.toFixed(1)} mm/h`, color: "text-amber-300" },
        ].map((item) => (
          <div key={item.label} className="rounded-xl bg-white/5 border border-white/10 p-3 text-center">
            <p className="text-xs text-slate-500 leading-tight mb-1">{item.label}</p>
            <p className={`font-mono text-sm font-bold ${item.color}`}>{item.val}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
