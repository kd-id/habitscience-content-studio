# Content Automation Studio — Antigravity Workspace Rules

This workspace hosts an end-to-end multi-platform content automation pipeline (Ideation -> Script & Repurposing -> Visual Assets -> Neural TTS & Subtitles -> FFmpeg 16:9 & 9:16 Video Rendering -> Auto-Draft / Auto-Publish -> Detailed Markdown & JSON Publish Report).

## Core Operating Rules

1. **Configuration first**: Always read `config/channel_config.yaml` before creating topics, scripts, or running renders so channel tone, niche, brand colors, voices, and target platforms match the user's setup.
2. **Safety on publishing**:
   - Default to `--publish-mode draft` (YouTube uploaded as `private` draft; social webhooks sent with `status: "draft"`) or `--publish-mode dry-run` when testing.
   - NEVER use `--publish-mode publish` (public live release) unless the user explicitly requests immediate public publishing.
3. **Agent-first intelligence**:
   - When running inside Antigravity, you may perform live web research (`search_web`), generate high-craft Indonesian/English scripts directly, optionally create hero visuals via `image-generator`, save the structured JSON brief, and invoke `python -m src.pipeline --brief <path>` so no external `GEMINI_API_KEY` is required.
4. **Always deliver the report**:
   - After every pipeline run, present the key findings and clickable file link to the generated `PUBLISH_REPORT.md` inside `output/<run_id>/`.
