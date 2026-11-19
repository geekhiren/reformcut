# Model and reasoning effort pickers

**User request:** Replace manual model typing with clickable available models, and add low/medium/high/extra-high effort selection.

**Approach:** Query the authenticated official app-server `model/list`, including pagination and each model's supportedReasoningEfforts/defaultReasoningEffort. Add native select controls to the existing subscription tab. Keep the automatic model and automatic effort choices for backward compatibility. Persist an optional reasoning_effort in ai.json and pass it to every Codex text/image invocation and connection test.

**Constraints:** Use the account's real catalog, not a fixed model-name list. Hide unsupported efforts, validate model/effort pairs server-side before any model call or settings write, and keep failed tests from replacing working settings. Preserve the current selection when merely viewing or testing it. Existing providers and old settings remain supported. Match the existing settings design.

1. Write failing tests for paginated model metadata, supported effort validation, settings persistence, CLI arguments and text/image dispatch. Add the admin-only catalog route and cache by Codex home/executable; invalidate on login/account change.
2. Replace the manual subscription input with model and effort selects. Update effort options on model change and make save/test intent explicit. Add retrieval failure/retry states and preserve existing selections while refreshing.
3. Run the complete suite, independent review, and actual browser verification. Restart only the idle current PeakCut instance; avoid running two servers on port 8765. Verify the selected effort is sent to Codex without changing the user's saved preference during UI testing.

**Progress:** Complete.

- Baseline and final full test suites passed. The focused suites contain 24 adapter tests and 27 subscription tests. New behavior was reproduced failing before implementation; independent review fixes also have failing-then-passing checks.
- Real model/list verified against the installed CLI: ten models and per-model efforts including low, medium, high, xhigh and, on some models, max and ultra. The server checks a fresh account-aware catalog before applying a choice and rejects unsupported pairs before calling Codex or saving settings.
- Independent review addressed: hidden fallback lists are explicitly replaced by the single-model selector when saved, with clear copy; in-flight tests lock both selectors and submission; the legacy Codex save path uses the same validation; failed catalog refreshes invalidate old data; unsaved choices survive retry.
- Live explicit low-effort request succeeded without saving a preference. Browser verification on the actual port 8765 selected GPT-6-Luna and Alto by click, confirmed its effort list omits Ultra, and preserved the draft through Check connection. Restored the unchanged automatic choice, verified controls are disabled while testing, and observed a successful real response.
- The existing idle instance was restarted once with updated code. Saved model remains default and saved effort remains automatic. Screenshot saved to the task's outputs folder.
