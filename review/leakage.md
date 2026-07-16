1. Are any scalers/normalizers (StandardScaler, MinMaxScaler, etc.) fit on
   the full dataset, or only on the train split?
2. Do any weather features use values that would not have been available
   as a *forecast* at prediction time (i.e. actuals leaking in)?
3. Are train/val/test splits strictly time-ordered, with no row-level
   shuffling across the split boundary?
4. Are all targets from the train timeframe without leakage from the prediction horizon?
5. Is empirical coverage (% of actuals falling inside each predicted band) measured against a held-out set and compared to the nominal level — not just assumed because pinball loss / conformal calibration was used?
6. Does the backtest simulate a decision using only information available before that interval's settlement (no peeking at the actual price/outcome to choose the strategy)?
