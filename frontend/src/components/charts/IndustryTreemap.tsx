import { ResponsiveContainer, Treemap, Tooltip } from "recharts";
import { ChartEmptyState } from "./ChartCard";
import type { ScreenedStock } from "../../types";

interface Props {
  stocks: ScreenedStock[];
  onSelect?: (basicIndustry: string) => void;
}

const PALETTE = ["#c9a227", "#4fb3a0", "#e8c766", "#e0793c", "#7fb8ff", "#d9694f", "#4fb3a0", "#e0793c", "#e8c766", "#e8c766"];

function colorFor(macroSector: string, index: Map<string, number>) {
  if (!index.has(macroSector)) index.set(macroSector, index.size);
  return PALETTE[index.get(macroSector)! % PALETTE.length];
}

interface TreeNode {
  name: string;
  size: number;
  count: number;
  macroSector: string;
  fill: string;
}

function CustomCell(props: { x?: number; y?: number; width?: number; height?: number; name?: string; fill?: string; count?: number; onSelect?: (n: string) => void }) {
  const { x = 0, y = 0, width = 0, height = 0, name, fill, count, onSelect } = props;
  const showLabel = width > 60 && height > 28;
  return (
    <g onClick={() => name && onSelect?.(name)} style={{ cursor: onSelect ? "pointer" : "default" }}>
      <rect x={x} y={y} width={width} height={height} fill={fill} fillOpacity={0.82} stroke="var(--bg-base)" strokeWidth={2} rx={4} />
      {showLabel && (
        <>
          <text x={x + 8} y={y + 18} fontSize={11.5} fontWeight={600} fill="#fff">
            {(name?.length ?? 0) > (width / 7) ? `${name?.slice(0, Math.floor(width / 7))}…` : name}
          </text>
          <text x={x + 8} y={y + 33} fontSize={10} fill="rgba(255,255,255,0.75)">
            {count} stock{count === 1 ? "" : "s"}
          </text>
        </>
      )}
    </g>
  );
}

export default function IndustryTreemap({ stocks, onSelect }: Props) {
  const colorIndex = new Map<string, number>();
  const byIndustry = new Map<string, { size: number; count: number; macroSector: string }>();

  for (const s of stocks) {
    const cap = s.market_cap_cr ?? 0;
    const key = s.basic_industry;
    if (!byIndustry.has(key)) byIndustry.set(key, { size: 0, count: 0, macroSector: s.macro_sector });
    const entry = byIndustry.get(key)!;
    entry.size += cap;
    entry.count += 1;
  }

  const data: TreeNode[] = Array.from(byIndustry.entries())
    .map(([name, v]) => ({
      name, size: v.size || 1, count: v.count, macroSector: v.macroSector,
      fill: colorFor(v.macroSector, colorIndex),
    }))
    .sort((a, b) => b.size - a.size);

  if (data.length === 0) return <ChartEmptyState message="No stocks match the current filter" />;

  return (
    <ResponsiveContainer width="100%" height={260}>
      <Treemap
        data={data}
        dataKey="size"
        aspectRatio={4 / 3}
        stroke="var(--bg-base)"
        content={<CustomCell onSelect={onSelect} />}
        isAnimationActive={false}
      >
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const p = payload[0].payload as TreeNode;
            return (
              <div style={{
                background: "var(--bg-card)", border: "1px solid var(--border-subtle)",
                borderRadius: 10, padding: "8px 10px", fontSize: 12,
              }}>
                <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>{p.name}</p>
                <p style={{ color: "var(--text-secondary)" }}>{p.macroSector}</p>
                <p style={{ color: "var(--text-dim)" }}>{p.count} stocks · ₹{p.size.toLocaleString("en-IN", { maximumFractionDigits: 0 })} Cr combined</p>
              </div>
            );
          }}
        />
      </Treemap>
    </ResponsiveContainer>
  );
}
