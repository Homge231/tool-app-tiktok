---
description: Rules for sender, controller, hotkeys, and pipeline code
globs:
  - "src/pricetyper/senders/**"
  - "src/pricetyper/controller.py"
  - "src/pricetyper/pipeline.py"
  - "src/pricetyper/ui/hotkeys.py"
---

- Sender text must be ASCII and obey the configured output template. ADB accepts digits only.
- Do not retry a send after an error; a retry can create duplicate chat messages.
- Check armed state both before creating a send decision and immediately before executing a sender action.
- Sender preparation must complete before state becomes ARMED.
- Use exactly one serial sender worker. Create, use, and close all Playwright synchronous API objects on the same worker thread.
- `dry_run` may produce send decisions in logs, but it must replace the selected sender with NullSender and must not launch a browser, click, type, or use ADB.
- PyAutoGUI `FailSafeException` must disarm. Three consecutive send failures return to LISTENING.
- Panic clears armed state, requests stop, closes the sender with a bounded wait, logs STOPPED, and exits with code 130.
- Never inspect message lists, chat contents, credentials, or cookies. `discover` may inspect visible input element attributes only.
- Use the local fake page for Playwright interaction checks. Block the latency sender benchmark when the active URL matches TikTok.
- The YouTube prototype is recognition-only. Its test-only launcher must force `NullSender`, must not create a real sender, and must never navigate to TikTok or submit a chat message.
- The separate `--tiktok-web` mode is an explicit Windows/Chromium-extension prototype. It starts disarmed and dry-run, defaults to filling an unsubmitted number draft, and only processes finalized ASR events. After probing the selected Live tab, the user may explicitly enable submit; an action then requires leaving dry-run and pressing F8. For submit, fill `@<number>` and click one uniquely identified visible send button associated with the chat input. Never dispatch Enter as a fallback or retry an action. Treat the click as unverified; do not claim the comment appeared.
- In `--tiktok-web`, allow audio only from TikTok Live URLs and revalidate the active TikTok host/live URL immediately before each sender action. Never inspect chat messages or comment lists; `discover` may inspect only visible input attributes.
- In `--tiktok-web`, partial ASR candidates may be shown but must not create fill or submit decisions; only finalized ASR events may create actions.
- Order visible-input selectors from site-specific to generic. Prefer TikTok's `[data-e2e="room-chat-input-field"]` when it uniquely identifies an editable visible field; if that selector matches multiple fields, abstain. Use generic editable selectors only when the specific selector has no visible match.
- Cross-browser sender work must act in the same user-selected TikTok Live tab that supplied audio, or explicitly prove that the capture and sender tabs are the same user session. Do not silently launch another branded browser or a second unrelated profile. Keep each browser-specific sender behind an adapter and mark it supported only after a local fake-page test and an interactive browser check.
