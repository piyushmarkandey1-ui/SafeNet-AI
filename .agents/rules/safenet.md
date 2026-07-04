# SafeNet AI — Workspace Rules

These rules apply to **all** agent-generated code, documentation, and data within this
workspace. Every contributor (human or AI) must follow them.

---

## 1. Synthetic Data Integrity

- All fake / generated / mock datasets **must** include the word `SYNTHETIC` in the
  filename (e.g., `calls_SYNTHETIC_2024.csv`).
- Every file that contains synthetic data **must** begin with a comment:
  ```
  # ⚠️  SYNTHETIC DATA — Not derived from real incidents or persons.
  ```
- Never claim that synthetic data is real in generated documentation, UI copy, or
  presentation materials.

## 2. FastAPI & Pydantic Conventions

- Use **FastAPI** for all HTTP endpoints.
- Use **Pydantic v2** (`BaseModel`, `model_validator`, `ConfigDict`, etc.) for request /
  response schemas — do **not** use Pydantic v1 APIs.
- Always define explicit `response_model` on route decorators.

## 3. Dual-Interface Module Contract

Every module (`scam_detector`, `counterfeit_vision`, `fraud_graph`, `geospatial`,
`citizen_shield`) must expose:

1. **A clean REST endpoint** — a FastAPI router mounted in `backend/app/main.py`.
2. **A plain Python function** — importable by the orchestrator so it can call the module
   directly without an HTTP hop.

The Python function is the **source of truth**; the REST endpoint should be a thin wrapper
around it.

## 4. Documentation

- Write **docstrings** (Google-style) on every public function, class, and module.
- Keep the root `README.md` up to date with high-level architecture and quickstart
  instructions.

## 5. Secrets & Configuration

- Store all API keys, model paths, and sensitive config in **environment variables**.
- Load them via `python-dotenv` / `os.getenv` — **never hardcode** secrets.
- Provide a `.env.example` listing every required variable (without values).

## 6. Code Style

- Python: follow PEP 8; prefer `snake_case` for functions/variables, `PascalCase` for
  classes.
- TypeScript / JSX: follow the project ESLint config; prefer named exports.
- Use type hints everywhere in Python.
