import type { FilterRow, IndicatorName, Op, Timeframe } from "../types";

const INDICATORS: { value: IndicatorName; label: string; fields: { value: string; label: string }[] }[] = [
  { value: "rsi", label: "RSI", fields: [{ value: "value", label: "Value" }] },
  {
    value: "bollinger",
    label: "Bollinger Bands",
    fields: [
      { value: "percent_b", label: "%B" },
      { value: "upper", label: "Upper Band" },
      { value: "lower", label: "Lower Band" },
      { value: "middle", label: "Middle Band" },
      { value: "bandwidth", label: "Bandwidth" },
    ],
  },
  {
    value: "volume_strength",
    label: "Volume Strength",
    fields: [
      { value: "volume_ratio", label: "Volume Ratio (%)" },
      { value: "volume_score", label: "Volume Score (0–5)" },
    ],
  },
];

const OPS: { value: Op; label: string }[] = [
  { value: "lt", label: "<" },
  { value: "lte", label: "≤" },
  { value: "gt", label: ">" },
  { value: "gte", label: "≥" },
  { value: "eq", label: "=" },
  { value: "neq", label: "≠" },
];

const TIMEFRAMES: Timeframe[] = ["1D", "1W", "1H", "15M", "5M"];

function newFilter(): FilterRow {
  return {
    id: crypto.randomUUID(),
    indicator: "rsi",
    field: "value",
    timeframe: "1D",
    op: "lt",
    value: 35,
  };
}

interface Props {
  filters: FilterRow[];
  onChange: (rows: FilterRow[]) => void;
}

export function FilterBuilder({ filters, onChange }: Props) {
  function add() {
    onChange([...filters, newFilter()]);
  }

  function remove(id: string) {
    onChange(filters.filter((f) => f.id !== id));
  }

  function update<K extends keyof FilterRow>(id: string, key: K, val: FilterRow[K]) {
    onChange(
      filters.map((f) => {
        if (f.id !== id) return f;
        const next = { ...f, [key]: val };
        // Reset field when indicator changes
        if (key === "indicator") {
          const ind = INDICATORS.find((i) => i.value === val);
          next.field = ind?.fields[0].value ?? "value";
        }
        return next;
      }),
    );
  }

  return (
    <div className="space-y-2">
      {filters.map((f, i) => {
        const ind = INDICATORS.find((x) => x.value === f.indicator)!;
        return (
          <div key={f.id} className="flex flex-col gap-1.5 rounded-lg border border-gray-700 bg-gray-800/60 p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Filter {i + 1}</span>
              <button
                onClick={() => remove(f.id)}
                className="text-gray-600 hover:text-red-400 text-sm leading-none"
                title="Remove filter"
              >
                ✕
              </button>
            </div>

            {/* Indicator + Field */}
            <div className="flex gap-1.5">
              <select
                value={f.indicator}
                onChange={(e) => update(f.id, "indicator", e.target.value as IndicatorName)}
                className="flex-1 rounded bg-gray-900 border border-gray-700 text-gray-200 text-xs px-2 py-1.5 focus:outline-none focus:border-blue-500"
              >
                {INDICATORS.map((ind) => (
                  <option key={ind.value} value={ind.value}>
                    {ind.label}
                  </option>
                ))}
              </select>
              <select
                value={f.field}
                onChange={(e) => update(f.id, "field", e.target.value)}
                className="flex-1 rounded bg-gray-900 border border-gray-700 text-gray-200 text-xs px-2 py-1.5 focus:outline-none focus:border-blue-500"
              >
                {ind.fields.map((fld) => (
                  <option key={fld.value} value={fld.value}>
                    {fld.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Op + Value + Timeframe */}
            <div className="flex gap-1.5">
              <select
                value={f.op}
                onChange={(e) => update(f.id, "op", e.target.value as Op)}
                className="w-14 rounded bg-gray-900 border border-gray-700 text-gray-200 text-xs px-2 py-1.5 focus:outline-none focus:border-blue-500"
              >
                {OPS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <input
                type="number"
                value={f.value}
                step={f.indicator === "bollinger" && f.field === "percent_b" ? 0.01 : f.indicator === "volume_strength" && f.field === "volume_ratio" ? 5 : 1}
                onChange={(e) => update(f.id, "value", parseFloat(e.target.value))}
                className="flex-1 rounded bg-gray-900 border border-gray-700 text-gray-200 text-xs px-2 py-1.5 focus:outline-none focus:border-blue-500"
              />
              <select
                value={f.timeframe}
                onChange={(e) => update(f.id, "timeframe", e.target.value as Timeframe)}
                className="w-16 rounded bg-gray-900 border border-gray-700 text-gray-200 text-xs px-2 py-1.5 focus:outline-none focus:border-blue-500"
              >
                {TIMEFRAMES.map((tf) => (
                  <option key={tf} value={tf}>
                    {tf}
                  </option>
                ))}
              </select>
            </div>
          </div>
        );
      })}

      <button
        onClick={add}
        className="w-full rounded-lg border border-dashed border-gray-700 py-2 text-xs text-gray-500 hover:border-blue-600 hover:text-blue-400 transition-colors"
      >
        + Add Filter
      </button>
    </div>
  );
}
