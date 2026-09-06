# Securitisation Crisis Case Studies -- A Data-Analytics Lens

The brief asks for analysis of real-world securitisation crises "through a
data analytics lens." The point of this document is narrower than a general
history of each crisis: for each episode, what specific metric -- of the kind
this repository actually computes (vintage curves, roll rates, credit
enhancement, excess spread) -- would have shown the problem building, and how
early. These are educational analytics case studies, not reconstructions of
any specific transaction's legal or cash-flow terms.

## 1. US subprime mortgage RMBS/CDO crisis (2007-2008)

**What happened, briefly:** mortgage originators progressively loosened
underwriting standards (limited-documentation and adjustable-rate loans to
borrowers with weak credit history), while these loans were pooled into
residential mortgage-backed securities and re-packaged into CDOs. Rating
agencies assigned high ratings based on historical loss assumptions that did
not hold once home prices stopped rising nationally at the same time,
producing correlated defaults across geographies that diversification
assumptions had not priced in.

**What the data-analytics view would have caught, and when:**

- **Vintage curve divergence** (this repo's `Vintage Cumulative Net Loss
  Rate` measure): 2006 origination-vintage mortgage pools showed materially
  worse cumulative loss curves than 2003-2004 vintages at the *same* months-
  on-book, well before absolute default counts looked alarming in aggregate.
  A vintage-curve dashboard is specifically designed to surface this kind of
  underwriting-quality drift early, because it holds seasoning constant.
- **Credit enhancement adequacy** (`Credit Enhancement %` /
  `Class C Wipeout Flag` in this repo): enhancement levels were sized off
  historical loss correlation assumptions; the analytical failure was not
  running enough *severe*, correlated-shock scenarios (this repo's
  `stress_testing.py` "Severe stress" scenario exists precisely to answer
  "does the structure survive if losses are 2-3x, not 1.2x, the base case").
- **Concentration reporting** (`state_summary.csv` / `servicer_summary.csv`
  pattern): a pool with heavy geographic concentration in the fastest-
  appreciating (and therefore most price-correction-exposed) markets is a
  concentration-risk signal that a state-level breakdown, of the kind this
  repo's investor pack produces, is built to surface.

## 2. European structured-credit liquidity stress (2007-2011)

**What happened, briefly:** even structurally sound European ABS/RMBS deals
saw spreads widen sharply and market liquidity dry up, independent of actual
collateral performance, because short-term funding vehicles (conduits) that
held these securities lost access to commercial paper markets. This was
substantially a *liquidity* crisis layered on top of, and at times separate
from, a *credit* crisis.

**What the data-analytics view would have caught:**

- **Excess spread trend monitoring** (`3-Month Rolling Net Loss Rate` /
  `Excess Spread Trapping Trigger` measures in this repo): a widening gap
  between a pool's weighted average coupon and its realised loss rate is an
  early liquidity-cushion indicator distinct from a default-rate indicator --
  the framework in `waterfall_methodology.md` (residual-to-equity cashflow
  each period) is exactly the kind of series that should be tracked
  independently of headline default statistics.
- **Distinguishing collateral performance from market price**: a
  loan-level/pool-level performance dashboard (this repo's
  `collateral_performance_trend.csv`) that keeps moving in a stable, boring
  line while market spreads for similar paper are widening sharply is itself
  a data point -- it tells you the stress is external (funding/liquidity),
  not internal (collateral), which calls for a different response.

## 3. COVID-19 consumer-credit payment shock (2020)

**What happened, briefly:** widespread income disruption led to a sudden
spike in requested payment deferrals/moratoria across auto, credit-card and
consumer ABS, even though many borrowers' underlying creditworthiness had not
structurally changed -- this was a liquidity/income-timing shock, not
primarily an underwriting-quality shock, and it resolved faster than 2008
-era stress for pools where the labour-market disruption was temporary.

**What the data-analytics view would have caught, and how it differs from
case 1:**

- **Roll-rate and cure-rate tracking** (`Roll Rate 30 to 60` / `Cure Rate`
  measures in this repo, built off `dpd_snapshot_history.csv`'s
  `RollFlag`/`CureFlag`/`TransitionType` fields): 2020-era stress showed an
  unusual pattern -- a sharp initial jump into early-stage delinquency
  buckets, but an *elevated cure rate* out of those buckets once income
  support and deferral programs took effect, versus 2008-era stress where
  roll rates into deeper delinquency stayed high and cure rates stayed low.
  A transition-matrix view (not just a point-in-time DPD snapshot) is what
  distinguishes "temporary income shock" from "structural credit
  deterioration" in near-real time, which matters directly for whether a
  pool should be staged as Stage 2 (temporary, expected to cure) or move
  toward Stage 3.
- **RBI/regulatory SMA classification tracking**: for an India-focused pool
  like this one, monitoring the `RBI_SMA_Class` distribution
  (`RBI SMA-2 Exposure` measure) over the moratorium period specifically is
  the kind of granular, regulation-aware view that a generic DPD bucket
  alone does not provide, since moratorium periods can affect how days-past
  -due is computed.

## How to use this in the Risk Arena

`risk_arena/index.html` includes `gfc2008` and `covid2020` presets whose
stressed-PD/LGD/CPR inputs are calibrated (as documented assumptions, not
historical data) to reflect the *qualitative* difference between these two
episodes described above: 2008-style stress hits both PD and LGD hard and
suppresses prepayment sharply (correlated, structural), while COVID-style
stress raises PD by less, keeps LGD closer to base (collateral values held up
better), and suppresses prepayment moderately (temporary, partially
income-support-driven).
