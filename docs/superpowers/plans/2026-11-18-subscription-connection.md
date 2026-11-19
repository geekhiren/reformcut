# Subscription account connection implementation plan

**Goal:** Fix the actual Windows discovery failure and provide a dedicated AI subscription tab with an official browser login, account identity and a connection test.

**User authorization:** The user requested the dedicated tab and account connection after the original flow failed; earlier they explicitly authorized proceeding directly with implementation.

**Architecture:** Keep Python and the official Codex CLI. Discover the registered Windows application when the web server lacks the Codex session's PATH. Use the documented app-server stdio account protocol for account/read, account/login/start and account/login/cancel. The CLI owns tokens and refresh. Existing clip requests continue through the tested adapter and the same Codex home.

**Constraints:** Admin-only routes and existing same-origin protection; no passwords, API keys or token fields in the new page; only public account email/plan and official login URL. Login is started only by a button click, cancellable and bounded to ten minutes. The account is shared with Codex on this computer; cancelling a login never signs that account out. No automatic auth launch when viewing the page. Reuse the existing page palette and settings layout.

## Tasks

1. Reproduce missing executable outside Codex PATH; write a failing discovery test, resolve the Windows package registration with a hidden bounded PowerShell process, cache discovery, verify against the web server's environment.
2. Write failing protocol/connection tests. Implement bounded stdio JSON-RPC, explicit initialization, secret-free account normalization, a pending login state with cancel/expiry/process cleanup, and admin routes. Test logged-out, API-only, connected, pending, completion, error and cancellation.
3. Add an `AI subscription` settings tab and route. Show account/plan, connection state, browser login and cancel controls, model choice and use/test action. Poll only while pending and stop when navigating away. Link from the existing AI tab, preserving old URLs.
4. Run the full suite, review changes independently, restart the idle user's instance safely, and validate the actual port 8765 flow with an ordinary PATH. Save a screenshot of the new tab.

## Evidence and progress

- Before edits, GET /api/ai on the user's port 8765 reports codex selected but installed=false and ready=false. The same CLI is found inside the agent's PATH and logged in through ChatGPT.
- Windows Get-AppxPackage successfully resolves the Codex installation without relying on PATH or listing the protected WindowsApps directory.
- Baseline and final complete suites passed with UTF-8 and FFmpeg discovery enabled in the test environment. The account-connection test file contains 20 passing tests; the existing Codex adapter has 21 passing tests.
- Tasks 1–3 complete. Tests reproduced missing Windows discovery, missing routes, stale expiry callbacks, completed logins after the page closed, deadline propagation, and unsafe save-before-test behavior before the corresponding fixes.
- Independent review completed. Fixed the timer identity race and late success recognition, bounded Windows discovery by the clip request's remaining budget, added a retry control for pending checks, made unchanged-model testing read-only and activation test-before-save, and made the Windows simulation portable.
- Live official login start/cancel verified with an empty temporary CODEX_HOME: pending login URL used auth.openai.com; cancel returned disconnected. The user's shared account was not used for this login-flow test.
- Restarted the idle actual instance at port 8765 using ordinary machine/user PATH, without the Codex app's injected executable path. Verified installed=true, ready=true, connected=true and Plus account identification. The existing completed video and creator remained present; no live recordings or unfinished jobs were interrupted.
- Browser verification on /app/settings/subscription: account identity and plan displayed; Test subscription returned `Subscription is ready. default answered successfully.` The ai.json existence and modification timestamp were unchanged after testing. Screenshot saved in the task's outputs folder.
- Task 4 complete. The user's instance remains running with the updated code.
