# Build a Dedicated MACD Analysis Page

Create a completely separate **MACD Analysis** page in the application. Do not mix these controls with the existing RSI/Bollinger/scanner pages.

The purpose of this page is to scan stocks and classify their MACD condition based on:

* MACD histogram direction and strength
* Bullish/bearish histogram transitions
* MACD line vs Signal line crossover
* Whether the crossover occurs above or below the Zero/Midline
* Configurable SMA/EMA calculation methods
* Configurable MACD periods
* Configurable timeframe
* Multiple MACD condition filters

The UI should be clean, professional and suitable for a stock-analysis/screener application.

---

## 1. MACD Indicator Settings

Create an **Indicator Settings** section similar to TradingView's MACD settings.

### Inputs

#### Source

Dropdown:

* Close
* Open
* High
* Low
* HL2
* HLC3
* OHLC4

Default:

```text
Close
```

#### Fast Length

Default:

```text
12
```

User configurable.

#### Slow Length

Default:

```text
26
```

User configurable.

#### Signal Length

Default:

```text
9
```

User configurable.

---

## 2. Moving Average Type

Allow the user to independently select the MA type used for MACD and Signal calculation.

### Oscillator MA Type

Dropdown:

```text
EMA
SMA
```

Default:

```text
EMA
```

### Signal MA Type

Dropdown:

```text
EMA
SMA
```

Default:

```text
EMA
```

This is important.

Do NOT hard-code EMA.

The calculation should dynamically change based on the user's selection.

For example:

### EMA configuration

```text
Fast MA = EMA(source, 12)
Slow MA = EMA(source, 26)

MACD = Fast MA - Slow MA

Signal = EMA(MACD, 9)

Histogram = MACD - Signal
```

### SMA configuration

```text
Fast MA = SMA(source, 12)
Slow MA = SMA(source, 26)

MACD = Fast MA - Slow MA

Signal = SMA(MACD, 9)

Histogram = MACD - Signal
```

And support mixed configurations such as:

```text
Oscillator = EMA
Signal = SMA
```

or

```text
Oscillator = SMA
Signal = EMA
```

---

. Timeframe
Allow the user to select:
1 Hour
4 Hours
1 Day
1 Week
Default:
1 Day
The MACD calculation must be performed using the actual OHLC data for the selected timeframe.
For example:
1H → calculate MACD using 1-hour candles
4H → calculate MACD using 4-hour candles
1D → calculate MACD using daily candles
1W → calculate MACD using weekly candles
Do not calculate MACD on daily data and simply resample/display it as another timeframe.
The selected timeframe must flow through the entire MACD calculation and screening pipeline.
For example:
Selected Timeframe
        ↓
Fetch corresponding OHLC data
        ↓
Calculate Fast MA
        ↓
Calculate Slow MA
        ↓
MACD
        ↓
Signal
        ↓
Histogram
        ↓
Crossover Detection
        ↓
Histogram State
        ↓
Stock Filtering
Timeframe selector
Use:
Timeframe [ 1D ▼ ]
Options:
1H
4H
1D
1W
Do not include:
1M
Monthly
The same MACD settings (Fast Length, Slow Length, Signal Length, SMA/EMA selection) should work across all four timeframes.

----------

# 4. MACD Visualization

Create a dedicated MACD chart panel.

It should visually resemble the TradingView MACD shown in the reference screenshots.

Display:

### Histogram

Use four histogram states:

#### Strong Bullish

```text
Histogram > 0
AND
Histogram > previous Histogram
```

Meaning:

```text
Positive and increasing
```

This indicates bullish momentum is strengthening.

---

#### Weakening Bullish / Slightly Bullish

```text
Histogram > 0
AND
Histogram < previous Histogram
```

Meaning:

```text
Still positive
but decreasing
```

Example:

```text
+500
+450
+380
+300
+220
```

This should be classified as:

```text
Weak Bullish
```

or

```text
Bullish Momentum Fading
```

This is particularly important because the histogram can still be green/positive while bullish momentum is weakening.

---

#### Strong Bearish

```text
Histogram < 0
AND
Histogram < previous Histogram
```

Meaning:

```text
Negative and becoming more negative
```

Example:

```text
-100
-200
-350
-500
```

Classify this as:

```text
Strong Bearish
```

---

#### Weakening Bearish / Bearish Recovery

```text
Histogram < 0
AND
Histogram > previous Histogram
```

Meaning:

```text
Still negative
but moving toward zero
```

Example:

```text
-500
-400
-300
-200
-100
```

Classify this as:

```text
Bearish Momentum Fading
```

or

```text
Bearish Recovery
```

---

# 5. Histogram Direction Filter

Add a filter allowing the user to select one or more of:

```text
All

Strong Bullish
Weak Bullish / Bullish Fading

Strong Bearish
Weak Bearish / Bearish Fading
```

Also provide:

```text
Positive Histogram
Negative Histogram
```

as simpler filters.

---

# 6. MACD / Signal Line Crossovers

Detect actual MACD-line and Signal-line crossovers.

### Bullish Crossover

A bullish crossover occurs when:

```text
MACD[t-1] <= Signal[t-1]
AND
MACD[t] > Signal[t]
```

### Bearish Crossover

A bearish crossover occurs when:

```text
MACD[t-1] >= Signal[t-1]
AND
MACD[t] < Signal[t]
```

Do not classify every candle where MACD > Signal as a crossover.

A crossover must represent an actual transition from one side to the other.

---

# 7. Zero-Line / Midline Context

The Zero line is extremely important.

Display the MACD zero line prominently.

For every crossover, determine whether the crossover occurred:

### Bullish Crossover Below Zero

```text
MACD crosses above Signal
AND
crossover occurs while MACD/Signal are below Zero
```

Classification:

```text
Bullish Crossover Below Zero
```

This should be treated as a potentially stronger early bullish signal because bullish momentum is beginning to emerge from negative territory.

---

### Bullish Crossover Above Zero

```text
MACD crosses above Signal
AND
crossover occurs above Zero
```

Classification:

```text
Bullish Crossover Above Zero
```

---

### Bearish Crossover Above Zero

```text
MACD crosses below Signal
AND
crossover occurs while MACD/Signal are above Zero
```

Classification:

```text
Bearish Crossover Above Zero
```

This can indicate weakening bullish momentum.

---

### Bearish Crossover Below Zero

```text
MACD crosses below Signal
AND
crossover occurs below Zero
```

Classification:

```text
Bearish Crossover Below Zero
```

---

# 8. Crossover Filters

Create a dedicated **Crossover Filter**.

Options:

```text
All Crossovers

Bullish Crossover
Bearish Crossover

Bullish Crossover Below Zero
Bullish Crossover Above Zero

Bearish Crossover Above Zero
Bearish Crossover Below Zero
```

Also allow:

```text
Crossover within last N candles
```

Example:

```text
1 candle
3 candles
5 candles
10 candles
20 candles
```

Make N configurable.

---

# 9. Combined MACD Conditions

The user should be able to combine conditions.

For example:

### Example 1

```text
Bullish Crossover Below Zero
+
Histogram > 0
+
Histogram increasing
```

### Example 2

```text
Bearish Crossover Above Zero
+
Histogram < 0
```

### Example 3

```text
Positive Histogram
+
Histogram decreasing
```

This should identify stocks where:

```text
MACD is still bullish
but bullish momentum is fading.
```

### Example 4

```text
Negative Histogram
+
Histogram increasing toward Zero
```

This identifies:

```text
Bearish momentum fading / potential bullish recovery
```

---

# 10. MACD State Classification

Every stock should receive a clear MACD status.

Use classifications such as:

```text
STRONG BULLISH

BULLISH

BULLISH MOMENTUM FADING

BULLISH CROSSOVER BELOW ZERO

BULLISH CROSSOVER ABOVE ZERO

NEUTRAL

BEARISH MOMENTUM FADING

BEARISH

STRONG BEARISH

BEARISH CROSSOVER ABOVE ZERO

BEARISH CROSSOVER BELOW ZERO
```

The classification should be based on the latest available candle and recent crossover information.

Do not simply use MACD > 0 as the bullish/bearish classification.

Consider:

* Histogram sign
* Histogram direction
* MACD vs Signal
* Recent crossover
* Zero-line position

---

# 11. Scanner / Results Table

Create a MACD-specific results table.

Columns:

```text
Symbol
Company Name
Sector
Current Price

MACD
Signal
Histogram

Histogram Direction
Histogram State

MACD vs Signal

Crossover
Crossover Location

Crossover Bars Ago

Zero Line Status

MACD Status
```

Example:

| Symbol | MACD | Signal | Histogram | Histogram State | Crossover | Location   | Status           |
| ------ | ---: | -----: | --------: | --------------- | --------- | ---------- | ---------------- |
| ABC    |  125 |    110 |       +15 | Increasing      | Bullish   | Above Zero | Strong Bullish   |
| XYZ    |   80 |     65 |       +15 | Decreasing      | None      | Above Zero | Bullish Fading   |
| DEF    |  -20 |    -35 |       +15 | Increasing      | Bullish   | Below Zero | Bullish Recovery |
| PQR    | -120 |    -80 |       -40 | Decreasing      | Bearish   | Below Zero | Strong Bearish   |

---

# 12. Quick Filter Presets

Add convenient presets so the user doesn't have to manually configure every condition.

### Strong Bullish

```text
Histogram > 0
AND Histogram increasing
AND MACD > Signal
```

### Bullish Momentum Fading

```text
Histogram > 0
AND Histogram decreasing
```

### Bullish Crossover Below Zero

```text
Recent bullish MACD crossover
AND crossover occurred below Zero
```

### Bearish Momentum Fading

```text
Histogram < 0
AND Histogram increasing toward Zero
```

### Strong Bearish

```text
Histogram < 0
AND Histogram decreasing
AND MACD < Signal
```

### Bearish Crossover Above Zero

```text
Recent bearish MACD crossover
AND crossover occurred above Zero
```

---

# 13. Custom Filter Builder

Also provide an advanced filter builder.

Allow conditions such as:

```text
MACD
Signal
Histogram
Histogram Change
MACD - Signal
Distance from Zero
Crossover Bars Ago
```

Operators:

```text
>
<
>=
<=
=
Crosses Above
Crosses Below
Increasing
Decreasing
```

Example:

```text
Histogram > 0
AND Histogram Change < 0
```

or:

```text
MACD Crosses Above Signal
AND MACD < 0
```

or:

```text
Histogram > 0
AND Histogram decreasing
AND MACD > Signal
```

---

# 14. Visual MACD Chart for Selected Stock

When the user clicks a stock from the results table, open/show a detailed MACD chart.

Display:

```text
Histogram
MACD Line
Signal Line
Zero Line
```

Mark crossover points directly on the chart.

For example:

```text
▲ Bullish Crossover
▼ Bearish Crossover
```

Also visually distinguish:

```text
Increasing positive histogram
Decreasing positive histogram
Increasing negative histogram
Decreasing negative histogram
```

The chart should closely follow the visual behavior of the TradingView MACD reference.

---

# 15. Indicator Settings UI

Create an expandable settings panel:

```text
MACD Settings

Source              [ Close ▼ ]

Fast Length         [ 12 ]

Slow Length         [ 26 ]

Signal Length       [ 9 ]

Oscillator MA       [ EMA ▼ ]

Signal MA           [ EMA ▼ ]

Timeframe           [ Daily ▼ ]
```

Then:

```text
Histogram Filters

☐ Strong Bullish
☐ Weak Bullish
☐ Strong Bearish
☐ Weak Bearish
☐ Positive
☐ Negative
```

Then:

```text
Crossover Filters

☐ Bullish Crossover
☐ Bearish Crossover

☐ Bullish Below Zero
☐ Bullish Above Zero

☐ Bearish Above Zero
☐ Bearish Below Zero

Crossover within [ 5 ] candles
```

---

# 16. Important Calculation Rules

Do not introduce look-ahead bias.

All crossover and histogram classifications must use only data available at that candle.

For example, bullish crossover detection must use:

```text
previous MACD <= previous Signal
current MACD > current Signal
```

not future candles.

Similarly:

```text
Histogram increasing =
Current Histogram > Previous Histogram
```

and:

```text
Histogram decreasing =
Current Histogram < Previous Histogram
```

Do not use future data to determine the current MACD state.

---

# 17. Architecture

Keep this page modular.

Create a dedicated MACD calculation/service layer rather than putting calculations directly inside the UI.

Suggested structure:

```text
MACD Page
    ↓
MACD Filter Configuration
    ↓
MACD Calculation Service
    ↓
MACD State / Crossover Detection
    ↓
Stock Scanner
    ↓
MACD Results
    ↓
Chart / Table
```

The calculation engine should be reusable by the backend scanner/API.

---

# 18. Persistence

Save the user's MACD settings so that reopening the MACD page retains the previous configuration.

Persist:

```text
Source
Fast Length
Slow Length
Signal Length
Oscillator MA Type
Signal MA Type
Timeframe
Histogram Filters
Crossover Filters
Crossover Lookback
```

Also provide:

```text
Reset to Defaults
```

Default configuration:

```text
Source = Close
Fast = 12
Slow = 26
Signal = 9
Oscillator MA = EMA
Signal MA = EMA
Timeframe = Daily
```

---

# 19. Important UX Requirement

The MACD page should NOT feel like a generic indicator settings page.

It should feel like a dedicated **MACD Stock Screener / Analysis Workspace**.

At the top show summary cards such as:

```text
Bullish Stocks       42
Bullish Fading       18
Recent Bullish Cross 11
Bearish Stocks       31
Bearish Fading       14
Recent Bearish Cross 8
```

Then show:

```text
Filters
    ↓
MACD Results
    ↓
Selected Stock MACD Chart
```

The user should be able to quickly answer:

> "Which stocks currently have strengthening bullish MACD momentum?"

> "Which stocks have a bullish crossover below the zero line?"

> "Which stocks are still bullish but their histogram is fading?"

> "Which stocks have recently turned bearish?"

> "Which stocks have bearish momentum fading and may be recovering?"

---

# 20. Keep Existing Pages Unchanged

Do not break or modify the existing RSI, Bollinger Band, volume, sector or other scanner functionality.

The MACD functionality should be implemented as a **separate page/module** with its own:

* UI
* settings
* filters
* calculations
* scanner
* results
* chart

Reuse existing database/API/stock-data infrastructure wherever possible instead of duplicating it.

Before implementing, inspect the existing project architecture and follow the current project's naming conventions, component structure, API patterns and styling system.
