# backend/app/indicators/registry.py — Beginner Explanation

> **Source file:** `backend/app/indicators/registry.py`

---

## 1. What is this file?

A lookup table that maps indicator names (strings) to their plugin objects. Any part of the codebase that needs to compute an indicator calls `indicator_registry.get("rsi")` and gets back the plugin that knows how to compute RSI from OHLCV bars.

---

## 2. The registry pattern

This is the **registry pattern** — a central dictionary that maps names to implementations. It decouples callers from specific plugin classes: the screening service doesn't import `RSIPlugin` directly; it just asks the registry for `"rsi"` and trusts that something useful comes back.

```python
class IndicatorRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, Any] = {}

    def register(self, plugin: IndicatorPlugin) -> None:
        self._plugins[plugin.name] = plugin   # key = plugin.name e.g. "rsi"

    def get(self, name: str) -> Any:
        plugin = self._plugins.get(name.lower())
        if plugin is None:
            raise ValueError(f"Unknown indicator: {name}")
        return plugin
```

`get()` lowercases the name before lookup, so `"RSI"` and `"rsi"` both work.

---

## 3. Registered plugins

```python
indicator_registry = IndicatorRegistry()
indicator_registry.register(rsi_plugin)              # "rsi"
indicator_registry.register(bollinger_plugin)        # "bollinger"
indicator_registry.register(volume_strength_plugin)  # "volume_strength"
indicator_registry.register(rsi_momentum_plugin)     # "rsi_momentum"
```

Each plugin is a module-level singleton (one instance shared across all requests). Plugins are stateless — they take bars and params as inputs, return a result, and hold no per-request state.

---

## 4. How the registry is used

The **ScreeningService** calls the registry to compute indicators for each stock:

```python
# Inside _fetch_indicator_for_stock():
plugin = indicator_registry.get(indicator_name)   # e.g. "rsi"
result = indicator_engine.calculate(bars, [indicator_name], ...)
```

The **IndicatorEngine** (in `indicators/engine.py`) also calls the registry internally when running `calculate()`.

---

## 5. Adding a new indicator

1. Create `backend/app/indicators/plugins/my_indicator.py` with a plugin class and singleton
2. Add `from app.indicators.plugins.my_indicator import my_indicator_plugin` at the top of this file
3. Add `indicator_registry.register(my_indicator_plugin)` at the bottom

The registry, filter engine, and scoring engine all pick up the new indicator automatically — no other files need changes for the indicator itself to be computable.
