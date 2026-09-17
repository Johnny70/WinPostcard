AHA CODE DIRECTIVE — Core Edition v2
Aligned with AHA CODE DIRECTIVE v1.2

Focus: simple, direct, concrete, stable and deterministic code.

============================================================
1. CORE PRINCIPLES
============================================================

- Always write the simplest code that correctly solves the task.
- Prefer explicit over implicit. Prefer concrete over abstract.
- Clarity and stability override all other concerns.
- No fuzzy logic, no guessing, no hidden behaviour.

============================================================
2. SIMPLICITY & CLARITY
============================================================

- Prefer straightforward, concrete implementations.
- Names must be self-explanatory.
- Code flow must be linear and easy to follow.
- Write out all steps explicitly, even if longer.

============================================================
3. STABILITY & ERROR HANDLING
============================================================

- Validate all input before running logic.
- No silent errors. No swallowed exceptions.
- No try/catch without logging.
- Assume external systems can fail and handle it explicitly.

============================================================
4. PREDICTABILITY
============================================================

- Same input → same output.
- No global state. No hidden mutation.
- No randomness unless explicitly required.
- Always return clear, machine-readable structures.

============================================================
5. MODULE STRUCTURE (MANDATORY)
============================================================

- One file = one responsibility.
- Every file must be fully understandable on its own.
- Every file begins with a header block:
  MODULE, RESPONSIBILITY, DEPENDS ON, EXPOSES.
- Max ~200 lines per file.
- Shared logic used by multiple files lives in dedicated modules.
- No god files. No vague “utils”.

============================================================
6. KATALOGSTRUKTUR (MANDATORY)
============================================================

- A directory = one responsibility.
- Max depth: 3 levels.
- Every directory must contain a README.md describing:
  - responsibility
  - contents
  - allowed dependencies
- Test directory must mirror src structure exactly.
- Only entrypoints, config and docs may exist in project root.

============================================================
7. DATA & TYPING
============================================================

- Be explicit about types, formats and structures.
- Document expected input and output.
- Python: type hints required.
- TypeScript: no implicit any; explicit return types.

============================================================
8. LOGGING
============================================================

- Log all errors.
- Logs must be clear and machine-readable.
- No vague logs (“error occurred”).

============================================================
9. TESTING (MANDATORY)
============================================================

- Every module/function must have at least one test.
- Tests must be deterministic (no time, randomness, network).
- Mock all external dependencies.
- Bug fixes require regression tests.

============================================================
10. REFACTORING (MANDATORY)
============================================================

- Remove old code immediately.
- No duplication. No commented-out code. No dead imports.
- A refactor is either 100% complete or not started.

============================================================
11. DEVLOG (MANDATORY)
============================================================

- Every session that modifies files must append an entry to:
  docs/devlog.json
- Format: ts, task, files, outcome, note.
- Append only after verifying correctness.

============================================================
12. CSS RULES (DETERMINISTIC MODE)
============================================================

- Only BEM selectors.
- Only longhand properties.
- Only design tokens (colors, spacing, typography, radii, shadows).
- No new selectors unless explicitly requested.
- No arbitrary values.
- No shorthands.

============================================================
13. ANTI-PATTERNS (NEVER ALLOWED)
============================================================

- Silent try/catch.
- Implicit type conversion.
- Unjustified magic values.
- Heuristic guesses.
- “Should work” solutions.
- Hidden dependencies.
- Global state affecting logic.
- Functions doing multiple things.
- Code requiring the reader to infer intent.

============================================================
14. VERIFICATION (MANDATORY)
============================================================

- Always read modified files after editing.
- Confirm correctness before reporting completion.

============================================================
15. CLOSING PRINCIPLE
============================================================

All code must be:

- simple
- direct
- concrete
- stable
- deterministic
- non-fuzzy
- easy to reason about
- easy to extend without breaking

============================================================
16. SECURITY (MANDATORY)
============================================================

- All external input is hostile by default.
- No execution, no access, no network call without explicit validation.
- Only whitelisted paths, formats, domains and protocols are allowed.
- All security‑relevant failures must log clearly and stop execution.
- Any component that cannot be proven secure is invalid and must not ship.