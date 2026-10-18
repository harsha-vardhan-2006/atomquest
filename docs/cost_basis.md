# Cost basis (replaces the old BOM figures)

All prices are **planning estimates in INR, not supplier quotations**. They are order-of-magnitude only.
Method: line-by-line low/high range per part, summed, plus 10 % contingency. Full line items are in `data/bom_ranges.csv`
(copy of the workspace ledger). The legacy fixed per-item BOM stays in `data/bom.csv` for traceability only and is
superseded by this basis; last reconciled 18 Oct 2026 with the Round 1 abstract upload file.

| Scope | Lines (low–high) | With 10 % contingency | Central |
|---|---|---|---|
| Round 2 Level 1 prototype (low-voltage control demonstrator, no rotor) | 6,400–13,000 | 7,040–14,300 | ≈ 10,700 |
| One full-fan prototype (CFRP rotor, 24 V BLDC + FOC, pan/tilt head) | 15,600–29,900 | 17,160–32,890 | ≈ 25,000 |

Notes
- The earlier figure (≈ INR 26,650 per fan) sits inside the full-fan range, so the full-fan estimate barely changes.
  The large reduction applies to the Round 2 Level 1 prototype, which is what the build plan actually requires.
- Prices are small-batch/prototype prices. Volume manufacturing would be far lower (for scale, ordinary retail BLDC
  ceiling fans in India are listed at roughly INR 3,000–12,000), but a retail fan has no pan/tilt head, CFRP rotor or dual MCUs.
- Excluded: custom blade tooling/moulds, test equipment, certification, shipping, GST differences.
- The old "≈ INR 5.8 lakh for a 3-fan programme" figure was removed from the abstract because its breakdown
  could not be reconciled with 3 x per-fan cost. Reinstate it only if data/bom.csv documents what it included.
- Unresolved, same as before: moving-mass roll-up 7.00 vs 6.80 kg; containment margin 128.8 J vs 130 J.
