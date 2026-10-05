from typing import Any
from app.technical.indicators.plugin import IndicatorPlugin
from app.technical.indicators.plugins.rsi import rsi_plugin
from app.technical.indicators.plugins.bollinger import bollinger_plugin
from app.technical.indicators.plugins.volume_strength import volume_strength_plugin
from app.technical.indicators.plugins.rsi_momentum import rsi_momentum_plugin
from app.technical.indicators.plugins.macd import macd_plugin
from app.logger import logger


class IndicatorRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Any] = {}

    def register(self, plugin: IndicatorPlugin) -> None:
        self._plugins[plugin.name] = plugin
        logger.debug("Indicator plugin registered", name=plugin.name)

    def get(self, name: str) -> Any:
        plugin = self._plugins.get(name.lower())
        if plugin is None:
            raise ValueError(f"Unknown indicator: {name}")
        return plugin

    def list_available(self) -> list[str]:
        return list(self._plugins.keys())


indicator_registry = IndicatorRegistry()
indicator_registry.register(rsi_plugin)
indicator_registry.register(bollinger_plugin)
indicator_registry.register(volume_strength_plugin)
indicator_registry.register(rsi_momentum_plugin)
indicator_registry.register(macd_plugin)
