---
name: content-automation-studio
description: >-
  End-to-end content automation workflow for YouTube (Long 16:9 & Shorts 9:16),
  TikTok, Instagram Reels & Carousel, LinkedIn, X/Threads, and Facebook.
  Use this skill whenever the user asks to generate, repurpose, render,
  auto-draft, or publish social media and YouTube content automatically,
  or when running scheduled content production tasks.
---

# Content Automation Studio Skill

Use this skill to produce complete multi-platform content packs—from trend research and master scripting to neural voiceover, synced `.srt` subtitles, thumbnail & 5-slide carousel design, HD FFmpeg 16:9 + 9:16 videos, auto-draft/auto-publish, and a detailed `PUBLISH_REPORT.md`.

**Project Root**: `C:\Users\Administrator\.gemini\antigravity\scratch\content-automation-studio`

## Standard Operating Procedure

### 1. Inspect Channel Brand & History
1. Read `C:\Users\Administrator\.gemini\antigravity\scratch\content-automation-studio\config\channel_config.yaml` to align niche, language, tone, voice, and target platforms.
2. Read `C:\Users\Administrator\.gemini\antigravity\scratch\content-automation-studio\output\history.json` (if present) so you never repeat a previously published topic.

### 2. Research & Author Master Blueprint (Agent-First Mode)
1. If the user did not specify a topic, run `search_web` for the latest trends matching `channel.niche` and `trends.queries`.
2. Draft a high-craft JSON blueprint matching the schema expected by `src/scriptwriter.py`:
   - `meta`: `topic`, `angle`, `hook`, `source`, `keywords`, `channel_name`, `channel_handle`, `language`
   - `youtube_long`: `title`, `alt_titles`, `description`, `tags`, `thumbnail` (`badge`, `headline`, `subheadline`, `visual_prompt`), `scenes` (5 scenes with `scene_no`, `section`, `visual_headline`, `bullet_points`, `on_screen_callout`, `narration`, `visual_prompt`)
   - `shorts_reels_tiktok`: `title`, `hook_text`, `caption_yt_shorts`, `caption_tiktok`, `caption_ig_reels`, `hashtags`, `scenes` (4 punchy vertical scenes totaling < 55 seconds)
   - `carousel_social`: `title`, `slides` (5 slides with `slide_no`, `badge`, `headline`, `body`, `highlight`, `visual_prompt`), `caption_instagram`, `caption_linkedin`, `thread_x` (5 tweets), `post_threads`, `post_facebook`, `hashtags`
3. Save the blueprint JSON to `output/_agent_brief.json`.

> **Optional AI Artwork Upgrade**: If the user requests bespoke AI illustrations/backgrounds, invoke the `image-generator` subagent to save `thumbnail_bg.png`, `long_scene_1.png..5.png`, or `short_scene_1.png..4.png` into a custom assets folder and pass `--custom-assets <dir>` below.

### 3. Execute Local Media Render, Auto-Draft & Reporting
Run the pipeline from the project root:

```powershell
cd "C:\Users\Administrator\.gemini\antigravity\scratch\content-automation-studio"
python -m src.pipeline --brief "output\_agent_brief.json" --visual-style cozy_diorama --publish-mode draft
```

- **Saved Visual Styles (`--visual-style` or `config/channel_config.yaml -> video.engine_mode`)**:
  - `cozy_diorama` *(Studio v8.3, default)*: Cozy midnight-indigo 2D dioramas + expressive 6-mood blinking character + pastel cream highlight cards + Georgia bold serif karaoke subtitles (100% free, 16:9 & 9:16).
  - `minimal_line_story` *(Studio v7)*: Dark matte `#0E0E0E` minimalist thin-line stick-figure & vector micro-storytelling + wide-tracked ALL-CAPS monospace yellow-highlight subtitles (100% free, 16:9 & 9:16).
  - `cinema_broll_html` *(Studio v6)*: Real HD cinema B-roll fast cuts + HTML5/CSS3/SVG frosted-glass Vox & Bento motion overlays + cinema SFX + animated `.ass` subtitles.
  - `flat_vector_2d` *(Studio v5)*: Kurzgesagt / TED-Ed 30fps flat vector 2D explainer.

- **Publish Modes**:
  - `--publish-mode dry-run`: Full render + QA + report without external uploads.
  - `--publish-mode draft` *(default & safest)*: Uploads YouTube Long & Shorts as `private` drafts (when OAuth is connected) and dispatches `status: "draft"` to social webhooks (Zapier/n8n).
  - `--publish-mode publish`: Live public release. **ONLY use when the user explicitly requests immediate public publishing.**

### 4. Multi-Agent Parallel Option (`run_workflow`)
For deep research + specialized copywriters per platform in parallel, execute:
`workflows/content_pipeline_workflow.py` using Antigravity's `run_workflow` tool with `Args={"topic": "...", "publish_mode": "draft"}`.

### 5. Present the Executive Publish Report
After completion, read `PUBLISH_REPORT.md` from the new `output/<run_id>/` directory and reply to the user with:
- Topic & key angle selected
- Platform status table (Auto-Drafted / Published / Dry-Run / Pending Credentials)
- QA checklist verification status
- Clickable `file://` links to `PUBLISH_REPORT.md`, `video_16x9.mp4`, `video_9x16.mp4`, `thumbnail.png`, and carousel slides.
