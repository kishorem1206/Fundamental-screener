import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface Props {
  value: number | null | undefined;
  label?: string;
  size?: number;
}

function scoreColor(v: number | null | undefined) {
  if (v === null || v === undefined) return "#6f7c96";
  if (v >= 75) return "#4fb3a0";
  if (v >= 55) return "#c9a227";
  if (v >= 40) return "#e0793c";
  return "#d9694f";
}

export default function ScoreGauge({ value, label = "Overall Score", size = 148 }: Props) {
  const v = value ?? 0;
  const color = scoreColor(value);
  const data = [{ name: "score", value: v, fill: color }];

  return (
    <div className="flex flex-col items-center justify-center" style={{ width: size, height: size }}>
      <div style={{ width: size, height: size, position: "relative" }}>
        <RadialBarChart
          width={size}
          height={size}
          cx="50%"
          cy="50%"
          innerRadius="72%"
          outerRadius="100%"
          barSize={10}
          data={data}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar background={{ fill: "var(--bg-input)" }} dataKey="value" cornerRadius={99} />
        </RadialBarChart>
        <div
          className="absolute inset-0 flex flex-col items-center justify-center"
          style={{ pointerEvents: "none" }}
        >
          <span className="text-3xl font-bold tabular-nums" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
            {value !== null && value !== undefined ? value.toFixed(0) : "—"}
          </span>
          <span className="text-[10px]" style={{ color: "var(--text-dim)" }}>/ 100</span>
        </div>
      </div>
      <p className="eyebrow mt-2 text-center">{label}</p>
    </div>
  );
}
