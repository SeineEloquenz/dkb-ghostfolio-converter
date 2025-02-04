# dkb-to-ghostfolio
This script parses account statements downloaded from DKB and generates a ghostfolio compatible json file to import.

Note: The regex to parse the ISIN is crudely hacked together, so might fail for you. If you have a suggestion how the ISIN can be better filtered, let me know!

Combine this with [ghostfolio-feeder](https://github.com/marco-ragusa/ghostfolio-feeder) to get current market data for the ISINs.
