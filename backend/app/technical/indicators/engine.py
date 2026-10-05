import dataclasses
from app.technical.indicators.plugin import OHLCVBar, IndicatorResult, TechnicalSnapshot, DataProvenanceItem
from app.technical.indicators.registry import indicator_registry
from app.technical.shared.utils import now_iso
from app.logger import logger


class IndicatorEngine:
    def calculate(
        self,
        bars: list[OHLCVBar],
        indicator_names: list[str],
        symbol: str,
        exchange: str,
        timeframe: str,
        source: str,
        data_range: str,
    ) -> TechnicalSnapshot:
        last_bar = bars[-1] if bars else None
        results: dict[str, dict] = {}

        for name in indicator_names:
            name = name.lower().strip()
            try:
                plugin = indicator_registry.get(name)
                result: IndicatorResult = plugin.calculate(bars, plugin.default_params)
                results[name] = {
                    "params": result.params,
                    "signal": result.signal,
                    **result.values,
                }
            except ValueError as e:
                logger.warning("Unknown indicator requested", name=name, error=str(e))
                results[name] = {"signal": "UNKNOWN", "error": f"Indicator not supported: {name}"}
            except Exception as e:
                logger.error("Indicator calculation failed", name=name, error=str(e))
                results[name] = {"signal": "UNKNOWN", "error": "Calculation failed"}

        provenance = DataProvenanceItem(
            source=source,
            symbol=f"{symbol}.NS" if exchange.upper() == "NSE" else f"{symbol}.BO",
            timeframe=timeframe,
            bars_used=len(bars),
            data_range=data_range,
        )

        return TechnicalSnapshot(
            symbol=symbol.upper(),
            exchange=exchange.upper(),
            timeframe=timeframe,
            requested_at=now_iso(),
            data_date=last_bar.date if last_bar else "",
            last_price=last_bar.close if last_bar else None,
            indicators=results,
            provenance=[provenance],
        )


indicator_engine = IndicatorEngine()
