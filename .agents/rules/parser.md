---
description: Rules for Vietnamese price parsing, gating, and send decisions
globs:
  - "src/pricetyper/parsing/**"
  - "src/pricetyper/decision/**"
---

- Treat §6.4 and §6.5 in `docs/SPEC.md` as the source of truth.
- In YouTube recognition mode, display the latest parsed span's value as a number; bypass the price gate, including its minimum, context exclusions, countdown filter, and anchored-price requirement. For example, `SỐ CHÍN` must display `9` even though the price gate rejects it.
- In YouTube number preview only, an explicit ascending count beginning `một hai ba...` is split into individual spans (`1, 2, 3, ...`) instead of being merged into digit strings. Keep the default price parser's digit-by-digit conventions unchanged; for example, `một bốn không` remains `140` there.
- TikTok Web number mode also bypasses the price gate and splits explicit ascending count sequences. It considers the last parsed number in finalized text only when its value is 100–999 inclusive; if that last value is out of range, abstain instead of falling back to an earlier number in the same text. The separate price-oriented mode retains its gate. Number mode is only used in the explicitly selected TikTok prototype and does not change parser behavior in other modes.
- Keep the price gate for price-oriented sending and price-scope benchmark evaluation. YouTube number preview does not authorize any sender.
- Preserve NFC normalization, parse precedence, span boundaries, and the examples defined in §6.4; grouped Arabic thousands separators are normalized before tokenization.
- Price values are exact VND: bare numbers remain literal, while explicit `nghìn`, `ngàn`, or configured `k` tokens multiply by 1,000.
- Under the configured shorthand profile, preserve the user-labeled readings `một trăm bốn`/`một bốn không`/`trăm bốn` = 140 and `một một không`/`trăm mốt`/`một trăm mốt` = 110. Treat them as explicit prototype conventions, not universal Vietnamese equivalences; ambiguous forms require labeled data and must not be fuzzily guessed.
- A sequence of separately unit-marked amounts such as `hai nghìn ba nghìn` may produce two spans. Keep unmarked thousand-plus compounds such as `một nghìn hai trăm` unsupported and rejected.
- The default price gate minimum is 1,000 VND; numbers below the configured minimum are not price candidates. The minimum remains configurable.
- Do not add support for “triệu”, colloquial money words, or unsupported thousand-plus ranges unless scope and SPEC are explicitly updated.
- Keep shorthand interpretation, `k_tokens`, gate filters, cooldowns, and hold times configuration driven.
- Ambiguous candidates should be rejected according to the specified gate; never widen matching just to increase recall without labeled evidence.
- Add a regression case whenever semantics change. Do not edit expected outcomes merely to make a test pass.
- Keep elapsed time based on monotonic time; do not use wall-clock time for cooldown logic.
