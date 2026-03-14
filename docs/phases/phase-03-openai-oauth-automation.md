# Phase 03A - OpenAI OAuth Automation

## Goal

- Make Codex CLI setup usable from the web UI without manual shell work.
- Avoid the WindowsApps `Access is denied` path for `codex.exe`.
- Start ChatGPT OAuth from the app and keep the user informed until Codex is ready.

## Changes

- Added a Windows wrapper command: `codex_npx.cmd {args}`.
- Made the backend treat legacy `codex {args}` templates as the wrapper on Windows.
- Added environment inspection for `npm`, `npx`, global `@openai/codex` install state, `codex exec`, and `codex login status`.
- Added automatic global install with `npm install -g @openai/codex@latest` when Codex CLI is missing.
- Added a login launcher that opens `codex login --device-auth` in a new terminal window.
- Added UI actions for `Auto setup/login` and `CLI check`.
- Added client polling so the status box refreshes automatically after the login window is opened.
- Added an execution-time Codex override so OAuth translation forces `model_reasoning_effort="high"` and does not inherit an incompatible global `xhigh` setting.
- Reduced translation error noise by summarizing Codex CLI failures and falling back to stdout when the CLI writes an empty JSON file on failure.
- Added per-attempt Codex artifact logs: prompt files, command, stdout/stderr, raw response, parsed JSON.
- Added checkpoint-based resume so rerunning the same translation session continues from already translated items.
- Added compatible-session seeding so a new auto-mode OAuth run can reuse the most complete previous checkpoint for the same document set.
- Added automatic economy routing for OAuth runs: the default model is now `auto-codex-economy`.
- Added document-by-document execution so one completed file is written to Ren'Py output immediately before the next file starts.
- Added pass-through handling for obvious non-linguistic strings such as `old:...` markers and filenames so they do not consume API calls.
- Added non-retryable error detection so quota/auth failures halt the session cleanly instead of exploding into recursive split retries.

## Constraints

- ChatGPT OAuth still requires the user to complete the browser/device-auth confirmation.
- Full silent login is not possible because the authentication step is owned by OpenAI's login flow.
- Translation can still run through the wrapper even if the global install check says Codex is not installed yet, because `npx` can fetch the package on demand.

## Validation

- `cmd /c "codex_npx.cmd exec --help"`
- `python -m py_compile RBackend.py`
- `node --check webui.js`
- Browser verification:
  - OpenAI provider -> Codex OAuth mode
  - default command becomes `codex_npx.cmd {args}`
  - entering `codex {args}` and pressing `CLI check` auto-normalizes to the wrapper
  - status shows Codex ready instead of WindowsApps access-denied
- Translation verification:
  - `POST /translate` with `provider=openai`, `openai_auth_mode=oauth_cli`, `model_name=gpt-5.1-codex`
  - verified success on `tl/ko/auto.rpy` after overriding CLI reasoning effort to `high`
