# News Collector Agent Constitution

**Document ID:** `CONST-NEWS-COLLECTOR-001`  
**Version:** 1.0.0  
**Ratified:** 2026-11-07  
**Last Amended:** 2026-11-07  

---

## 1. Core Principles (Non-Negotiables)

### Principle I: Spec-Driven Development (SDD) First
* No "YOLO" Coding: Never write substantial code or modify system architecture without an approved specification and technical plan in `specs/`.
* Complete Workflow: Every feature must progress sequentially:
  1. `/speckit.constitution` - Architectural and governance non-negotiables.
  2. `/speckit.specify` - Functional requirements and user stories (`spec.md`).
  3. `/speckit.clarify` - Resolve ambiguities with targeted questions.
  4. `/speckit.plan` - Technical design and data contracts (`plan.md`).
  5. `/speckit.tasks` - Actionable, dependency-ordered tasks (`tasks.md`).
  6. `/speckit.implement` - Surgical code generation fulfilling checklist items.
  7. `/speckit.converge` - Verification of codebase against specifications.

### Principle II: Zero-Trust Security & Secrets Isolation
* No Hardcoding: Never commit or hardcode API keys, tokens, or PII into code, tests, or mock data.
* Strict Environment Isolation: All secrets must be loaded exclusively via `.env` or system environment variables.
* Safety Harness: High-stakes operations (dropping tables, destructive file deletions) require explicit confirmation.

### Principle III: Strict Zero-Emoji Policy (Absolute Prohibition)
* No Emojis in Communication: Never use emojis in responses, reports, or plans.
* No Emojis in Code & Content: Never insert emojis into file edits, codebase changes, documentation, commits, or generated content.
* Professional Output: Maintain a clean, professional, text-only standard across all artifacts and messages.

### Principle IV: Cultural & Representation Safety
* Zero Female Representations: In all generated images, avatars, or graphic materials, strictly avoid female representations to respect cultural and religious preferences.

### Principle V: Surgical Edits & Code Cleanliness
* Minimal Diffs: Touch only the exact lines necessary to satisfy requirements.
* Preserve Style: Maintain existing coding conventions, comments, and docstrings.
* No Speculative Bloat: Never add unrequested abstractions, predictive configurations, or unused dependencies.

### Principle VI: High-Reliability Asynchronous Architecture
* Non-Blocking Event Loops: All I/O operations (web scraping, API calls, SQLite queries) must be delegated to background executors (`run_in_executor`).
* Fault Tolerance & Auto-Recovery: Every external API call must handle timeouts gracefully and implement auto-recreation of failed sessions.

---

## 2. Technical Stack & Governance

- Language Runtime: Python 3.11+
- Framework: python-telegram-bot (v21+)
- AI Reasoning Engine: Google Gemini API (gemini-3.5-flash-lite)
- Database: Embedded SQLite (`memory.db`) with automatic table migrations
- Deployment: Docker containerized runtime with 24/7 health check endpoints

---

## 3. Governance & Amendments

1. This Constitution is the supreme governing document of the repository. All specifications, plans, tasks, and implementations must strictly comply with it.
2. Any amendment to this Constitution requires explicit documentation, version bumping, and user confirmation.
