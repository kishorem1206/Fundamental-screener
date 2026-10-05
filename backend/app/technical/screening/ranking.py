from app.technical.screening.dsl import RankSpec


def rank_results(stocks: list[dict], rank_by: RankSpec) -> list[dict]:
    """Sort screened stocks by indicator field. Stocks missing the value go last."""

    key = f"{rank_by.indicator.lower()}_{rank_by.timeframe.upper()}"

    def sort_key(stock: dict):
        val = stock.get("indicators", {}).get(key, {}).get(rank_by.field)
        # None values always go to the end regardless of order
        if val is None:
            return (1, 0)
        return (0, float(val))

    return sorted(stocks, key=sort_key, reverse=(rank_by.order == "desc"))
