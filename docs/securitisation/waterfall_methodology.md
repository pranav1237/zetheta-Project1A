# Securitisation Waterfall Methodology

`src/securitisation/waterfall.py` implements a sequential-pay (senior/mezz/
subordinate) cashflow waterfall, run month-by-month against the **actual**
pool performance in `data/securitisation/raw/dynamic_loss_monthly.csv`
(`CollectionsTotal`, `NetLoss_ThisMonth`, `Prepayments_ThisMonth`,
`ScheduledAmort`) rather than a simulated cashflow.

## 1. Capital structure

The pool's first-month `BOP_Balance` (~INR 543M) is used to size a
representative three-class structure (`DEFAULT_TRANCHES` in `waterfall.py`):

| Class | % of pool | Coupon | Role |
|---|---|---|---|
| Class A (Senior) | 84% | 8.4% | First-priority interest & principal |
| Class B (Mezzanine) | 10% | 10.8% | Subordinate to A, senior to C |
| Class C (Subordinate/Equity) | 6% | 14.5% | First-loss piece; absorbs losses first |

This sizing (84/10/6) is a documented, project-level structuring assumption
consistent with how an arranger would typically size an investment-grade
senior class against a granular, seasoned Indian auto-loan pool with a
sub-2% observed loss rate -- it is **not** copied from any real transaction.

## 2. Waterfall mechanics, in order, each period

1. **Loss allocation (junior-to-senior):** `NetLoss_ThisMonth` writes down the
   subordinate balance first, then mezzanine, then senior only if losses
   exceed everything beneath it. This is the core credit-enhancement
   mechanic -- it is *why* Class A can carry investment-grade risk against a
   pool with meaningfully higher expected loss.
2. **Interest waterfall (sequential by priority):** each tranche's interest
   due (`ending_balance x coupon / 12`) is paid in priority order from that
   month's `CollectionsTotal` before any tranche below it receives a rupee.
3. **Principal waterfall (sequential):** remaining collections after interest
   pay down principal strictly in priority order -- Class A is retired in
   full before Class B receives any principal, and so on.
4. **Residual to equity:** whatever is left after all scheduled interest and
   principal is the `residual_to_equity` cashflow -- the pool's excess spread
   captured by the most junior holder.

## 3. What this demonstrates

Running `python -m src.securitisation.waterfall` over the 12 available
reporting months shows Class A's ending balance amortising steadily while
Class C absorbs the (currently modest) net losses -- i.e., the structure is
functioning as designed under base-case performance. `stress_testing.py`
re-runs the same waterfall with `NetLoss_ThisMonth` scaled up 1.5x/2.3x to
check **at what stress level Class C would be wiped out**
(`class_c_wiped_out` in `stress_results.csv`) -- the single most important
question a mezzanine/equity investor asks before buying into a deal.

## 4. What a production/legal waterfall adds that this doesn't

- Reserve-fund funding/draw mechanics and a documented reserve floor.
- Trigger-driven switches (e.g., cumulative-loss or delinquency triggers that
  convert a pro-rata structure to fully sequential).
- Servicing/trustee fees paid ahead of note interest.
- Clean-up call rights once the pool amortises below a threshold.
- Legal-document-specific definitions of "available funds," "principal
  collections," and "extraordinary principal" (e.g., insurance proceeds).

These are documented here as explicit scope boundaries, not silently assumed
away.
