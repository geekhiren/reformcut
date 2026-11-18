# Codex subscription implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let PeakCut use the installed Codex CLI with the owner's ChatGPT subscription, through a Python adapter, as Paperclip does.

**Architecture:** Add a `codex` provider to the existing AI boundary. A separate standard-library Python module owns executable discovery, subscription-login checks, isolated `codex exec` invocations, JSONL parsing, timeouts, images and usage. Existing AI providers keep their current protocols.

**Tech Stack:** Python 3.12 environment already installed here, subprocess, tempfile, unittest.mock, existing FastAPI and plain HTML settings.

**Spec:** User explicitly chose “Adaptador Python usando o Codex CLI; pode seguir direto com a implementação”. This plan records the implementation decisions below; execution continues inline without another approval gate.

## Global constraints

- Reuse CLI-managed ChatGPT authentication; never copy or expose auth tokens.
- Require subscription login and remove API-key overrides from child processes; never silently switch to API billing.
- Run each request in a temporary directory, read-only, without inherited user configuration, shell tools or web search. Pass prompts on stdin and use argument lists rather than a shell.
- Return the existing `(answer, tokens_in, tokens_out)` contract, including image requests; honor caller timeouts, including queueing and subprocess cleanup.
- Offer a `default` model and locally cached model choices; no API key or HTTP base URL for this provider.
- Preserve the existing page design and admin permissions; call `ctx.bump()` through existing settings routes.

## Review focus

- Windows executable and cmd wrappers; no accidental shell interpretation.
- API-key login or key environment variables must not become subscription usage.
- Truncated or failed JSONL must not be treated as successful model output.
- Timeout must stop the actual invocation and release the serialization lock.
- Images, Unicode, long transcripts and optional schema fields must keep their existing meanings.

### Task 1: Python CLI adapter

**Files:** Create `studio/codex.py`, `tests/test_codex.py`.

**Interfaces:** `codex.status() -> dict`, `codex.list_models() -> list[str]`, `codex.run(model, prompt, schema=None, image=None, timeout=None) -> tuple[str, int, int]`, `CodexError(RuntimeError)`.

- [x] Write tests for successful JSONL, terminal failures, absent completion, usage counts, subscription-login checks, missing executables, sanitized environment, stdin prompts, strict JSON schema, image lifecycle and process timeout.
- [x] Run `.venv/Scripts/python.exe tests/test_codex.py`; confirm missing adapter fails.
- [x] Implement the adapter using the installed CLI's supported flags and reusable CLI authentication. Serialize invocations to avoid excess concurrent subscription use; queue time belongs to the timeout budget.
- [x] Run the adapter tests; require all passing.

### Task 2: PeakCut integration and settings

**Files:** Modify `studio/ai.py`, `web/index.html`, `.env.example`, `README.md`, `tests/run.py`; extend `tests/test_codex.py`.

**Interfaces:** Existing `ai.call`, `ai.see`, `ai.ready`, `ai.public`, `ai.save`, `ai.list_models`, `ai.explain` gain the `codex` provider without changing their return types. Calls use Task 1's adapter.

- [x] Add failing tests for keyless settings, provider dispatch, error explanations, model listing, ignored stale API key/address and saved settings.
- [x] Implement provider registration and dispatch, hide irrelevant fields in settings, explain subscription login and quotas, document setup and `PEAKCUT_CODEX_COMMAND`.
- [x] Register the new test file in the suite and run focused AI/local-settings tests.
- [x] Run `.venv/Scripts/python.exe tests/run.py` and a small live CLI JSON request using the current subscription; inspect the final diff.

## Progress

- Existing checkout clean at start; feature branch `codex/codex-subscription` created in the requested folder. No separate worktree: changes must be available in the user's installed checkout.
- Baseline and final full suites passed. On this Windows session, tests need `PYTHONIOENCODING=utf-8` and the FFmpeg directory added by `studio.tools` discovery. The initial unadjusted baseline exposed those environment issues; production code did not need changes for them.
- Task 1 complete: tests first failed for the missing adapter, then passed. Task 2 complete: provider integration tests first failed, then passed. Final test file: 21 passing tests.
- Independent read-only reviewer found two Windows timeout failures and four protocol/state/tool-scope issues. Each was reproduced before the fix; all regression tests and the full suite passed afterward.
- Fixed native npm discovery (no Node parent), blocking Windows stdin (temporary UTF-8 file), optional schema fields (nullable strict representation with omissions restored), JSONL ordering/truncation and Unicode line separators, subscription-aware readiness with a five-second cache, and explicit feature restrictions with accurate documentation.
- Live verification: structured JSON with optional fields returned `{"items": [{"title": "ok"}]}`; synthetic red-image request returned `red`; the browser's Save and test returned `Saved. default answered, so the AI is ready.` Screenshot saved to the task's outputs folder.
- Browser verification used a separate temporary data directory and port 18765. The existing instance on port 8765 and its saved AI settings were left intact; it needs a restart to load the new provider.
