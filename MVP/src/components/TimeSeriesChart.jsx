import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Legend
} from "recharts";
import { LineChart as LineChartIcon } from "lucide-react";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-blue-400/20 bg-slate-900/95 backdrop-blur-md p-3 text-xs shadow-xl">
      <p className="font-semibold text-white mb-1.5">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2 text-slate-300">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span>{p.name}:</span>
          <span className="font-mono text-white">{Number(p.value).toFixed(1)} mm/h</span>
        </div>
      ))}
    </div>
  );
};

export default function TimeSeriesChart({ data }) {
  return (
    <div className="card-glow p-5">
      <div className="flex items-center gap-2 mb-5">
        <LineChartIcon className="w-4 h-4 text-blue-400" />
        <h3 className="font-semibold text-white text-sm uppercase tracking-wider">
          Precipitación Multiestación
        </h3>
        <span className="ml-auto text-xs text-slate-500">últimas 3h + pronóstico 1h</span>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="gradAvg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradCI" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#0ea5e9" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />

          <XAxis
            dataKey="time"
            tick={{ fill: "#64748b", fontSize: 11, fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 11, fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `${v}`}
          />

          <Tooltip content={<CustomTooltip />} />

          <ReferenceLine
            x="Ahora"
            stroke="rgba(251,191,36,0.4)"
            strokeDasharray="4 3"
            label={{ value: "AHORA", fill: "#fbbf24", fontSize: 10, fontFamily: "JetBrains Mono" }}
          />

          {/* IC superior e inferior */}
          <Area
            type="monotone"
            dataKey="q90"
            stroke="none"
            fill="url(#gradCI)"
            name="IC 90% sup."
            legendType="none"
          />
          <Area
            type="monotone"
            dataKey="q10"
            stroke="none"
            fill="white"
            fillOpacity={0}
            name="IC 90% inf."
            legendType="none"
          />

          {/* Media */}
          <Area
            type="monotone"
            dataKey="avg"
            stroke="#3b82f6"
            strokeWidth={2.5}
            fill="url(#gradAvg)"
            name="Promedio"
            dot={(props) => {
              const { payload, cx, cy } = props;
              if (!payload.forecast) return null;
              return (
                <circle key={`dot-${cx}`} cx={cx} cy={cy} r={4}
                  fill="#3b82f6" stroke="#1e3a5f" strokeWidth={2} />
              );
            }}
            strokeDasharray={(d) => d?.forecast ? "5 4" : undefined}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-6 h-0.5 bg-blue-400 rounded" />
          Promedio observado
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-6 h-0.5 border-t border-dashed border-blue-400 rounded" />
          Pronóstico
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-4 h-3 rounded bg-sky-400/20 border border-sky-400/30" />
          IC 90%
        </span>
      </div>
    </div>
  );
}
