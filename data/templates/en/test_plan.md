# Test Plan — [Module name]

**Project:** [Project name]
**Version:** [1.0]
**Purpose:** test cases verifying the software requirements of the [name] module.

> ⚠️ **Do not put anything confidential in it.** For the audit, this document is sent to
> an external AI service (Groq). Use a fictitious or anonymised project.
>
> How to use: replace everything in [brackets], keep the headings and the identifiers
> (TC-001, TC-002…). Copy one "TC-…" block per test case.

---

## 1. Scope

This plan describes the test cases for the requirements of the specification
[document name, version]. Each case references the requirement it verifies.

## 2. Test cases

### TC-001 — [Short title]
- Verifies: SRS-001
- Description: [stimuli, conditions, measurement].
- Expected result: [observable value or state, with unit].

*Each test case references at least one existing requirement (CHK-08).*

### TC-002 — [Short title]
- Verifies: SRS-002
- Description: [stimuli, conditions, measurement].
- Expected result: [observable value or state].

### TC-003 — [Short title]
- Verifies: SRS-003
- Description: [stimuli, conditions, response-time measurement].
- Expected result: [reaction within N unit].

## 3. Coverage matrix

*Every requirement covered by at least one test case (CHK-07, CHK-14); this matrix must
match the actual content of the specification and of the cases above (CHK-09).*

| Requirement | Test case |
|-------------|-----------|
| SRS-001     | TC-001    |
| SRS-002     | TC-002    |
| SRS-003     | TC-003    |
