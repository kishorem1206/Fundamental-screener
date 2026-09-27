from app.sectors.base import SectorFramework, SectorMetric


class GenericSector(SectorFramework):
    sector_name = "Generic"
    sector_aliases = []

    def key_metrics(self) -> list[SectorMetric]:
        return [
            SectorMetric("revenue_cagr_3y", "Revenue CAGR (3Y)", 0.12, "high", "higher_is_better", "%"),
            SectorMetric("ebitda_margin", "EBITDA Margin", 0.15, "high", "higher_is_better", "%"),
            SectorMetric("pat_margin", "PAT Margin", 0.10, "high", "higher_is_better", "%"),
            SectorMetric("roce", "ROCE", 0.15, "high", "higher_is_better", "%"),
            SectorMetric("roe", "ROE", 0.10, "high", "higher_is_better", "%"),
            SectorMetric("debt_to_equity", "D/E", 0.10, "high", "lower_is_better", "x"),
            SectorMetric("fcf_to_pat", "FCF/PAT", 0.10, "high", "higher_is_better", "%"),
            SectorMetric("cfo_to_pat", "CFO/PAT", 0.08, "medium", "higher_is_better", "%"),
            SectorMetric("current_ratio", "Current Ratio", 0.05, "medium", "higher_is_better", "x"),
            SectorMetric("interest_coverage", "Interest Coverage", 0.05, "medium", "higher_is_better", "x"),
        ]
