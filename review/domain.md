1. Are the timestamps of both ENTSO-E and Open-Meteo consistent
   (hourly, every 15 mins, etc.)?
2. Are both ENTSO-E timestamps and Open-Meteo timestamps in the
   correct timezone (UTC)?
3. Are the CET/CEST transitions of the timestamps and the daily aggregations corrupt?
   (test the last Sundays of March/October)
4. Is the power (MW) vs energy (MWh) conversion correct and consistent?
5. Are there no quantile crossings?
6. Does the LLM never compute statistics?
7. Does the LLM never assert facts absent from retrieved context?
8. Is the extraction output of the LLM validated against a JSON schema?
9. Does the LLM refuse out-of-corpus questions?
10. Is the imbalance settlement math at the correct interval length?
11. Are the settlement/transaction-cost assumptions used in the backtest (fees, interval length, which price applies) explicitly documented, not implicit in the code?
12. Where large forecast errors are reported, does the evaluation note whether the interval could reflect curtailment/redispatch/outages in the 'actual generation' figure, rather than attributing the error to the model outright?
13. If this diff is AI-origin and touches settlement rules, EEG provisions, or ENTSO-E field semantics, is there a cited source (spec, ENTSO-E documentation, EEG text) confirming it was verified rather than just plausible-sounding?
