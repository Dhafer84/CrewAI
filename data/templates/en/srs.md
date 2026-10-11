# Software Requirements Specification — [Module name]

**Project:** [Project name]
**Version:** [1.0]
**Context:** [One sentence: what the module does, in which system.]
**Target standards:** ASPICE (SWE.1 / SWE.2), ISO 26262 Part 6.

> ⚠️ **Do not put anything confidential in it.** For the audit, this document is sent to
> an external AI service (Groq). Use a fictitious or anonymised project.
>
> How to use: replace everything in [brackets], keep the headings and the identifiers
> (SRS-001, SRS-002…). Copy one "SRS-…" block per requirement. The notes in italics
> point to the audit checks (CHK-xx); delete them afterwards if you like.

---

## 1. Introduction

[What the module does, its inputs and outputs, what is out of its scope.]

## 2. Definitions

- **[Term]**: [definition, with unit if it is a quantity].
- **[Term]**: [definition].

## 3. Functional requirements

### SRS-001 — [Short title]
The module SHALL [a single, measurable behaviour].
- Acceptance criterion: [verifiable condition, with value and unit].
- Upstream trace: [SYS-REQ-xxx, or justification for no trace].

*One unique identifier per requirement (CHK-01); a measurable acceptance criterion
(CHK-02); no vague word such as "quickly" without a value (CHK-03); one need per
requirement, no "and" hiding two (CHK-04); an upstream trace (CHK-06).*

### SRS-002 — [Short title]
The module SHALL [behaviour].
- Acceptance criterion: [verifiable condition].
- Upstream trace: [SYS-REQ-xxx].

### SRS-003 — [Safety function: detection, fallback, protection]
If [condition], the module SHALL [reaction] within [duration] [unit].
- Acceptance criterion: [verifiable condition, bounded response time].
- Upstream trace: [SYS-REQ-xxx].

*Safety functions: deterministic behaviour (CHK-10), bounded response time (CHK-11),
consistent thresholds and hysteresis across related requirements (CHK-13).*

### SRS-004 — [Sensor or input failure]
If [invalid or out-of-range input], the module SHALL [safe fallback state].
- Acceptance criterion: [verifiable condition].
- Upstream trace: [SYS-REQ-xxx].

*Behaviour on failure is specified (CHK-12).*

## 4. Non-functional requirements

### SRS-005 — [Robustness, performance, memory…]
The module SHALL [measurable requirement].
- Acceptance criterion: [verifiable condition].
- Upstream trace: [SYS-REQ-xxx].
