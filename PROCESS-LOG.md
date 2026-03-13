# Process Log — RevenueCat Charts API Take-Home Assignment

**Agent:** Katire (autonomous AI agent)
**Operator:** Eduardo Muth Martinez
**Runtime:** OpenClaw · Claude Opus 4.6
**Started:** 2026-03-12 21:49 UTC
**Tools used:** OpenClaw, Claude Opus 4.6, RevenueCat Charts API V2, ElevenLabs TTS, OpenAI gpt-image-1, GitHub API, Notion API, ffmpeg

---

## Phase 1: Research (21:49-21:52 UTC)

- Fetched and analyzed RevenueCat Charts documentation
- Reviewed API V2 authentication, OAuth scopes, MCP tools reference
- Identified Charts API as new and under-documented publicly
- Reviewed Charts v3 (Beta) real-time reporting docs
- Assessed sandbox constraints: no Python, no curl, no network initially

**Key decision:** Build a Python CLI + library over a web app. Most useful form factor for both developers AND agents. Web apps need hosting; Python packages work anywhere.

## Phase 2: Initial Build (21:53-22:30 UTC)

- Built rc-insights v0.1.0: 4 Python modules, 3 example scripts
- Wrote blog post (1,689 words), 5 social posts, video script
- Designed growth campaign with 5 communities and $100 budget
- Created Notion submission page

**Constraint:** Sandbox had no Python runtime or network. Built from documentation patterns.

## Phase 3: Environment Upgrade + Live Testing (01:07-01:15 UTC)

- Sandbox upgraded with Python, curl, git, API keys
- Tested real Charts API endpoints, discovered actual response schema
- Rewrote client to match real API (zero dependencies, stdlib only)
- Verified against live Dark Noise data: MRR $4,538, 2,519 active subs, 56 trials
- Generated sample reports from real data
- Pushed to GitHub: github.com/Clueless-Creations/rc-insights

**Key discovery:** Charts API response uses unix timestamps in `cohort` field, `measure` index for multi-metric charts, `values` array (not `data`). 21 available chart types discovered via API error message pattern.

## Phase 4: Agent-Native Self-Evaluation (02:04-02:15 UTC)

Applied agent-native architecture principles against rc-insights:

**Violations found:**
- Analyzer was a workflow-shaped tool (bundles judgment into code)
- Chart names were statically mapped via Python enum
- No explicit completion signals for agent loops
- Thresholds were hardcoded, not agent-controllable
- No MCP server for agent discovery

**Fixes applied (v0.2.0):**
- Made analysis primitives public: `calc_trend()`, `detect_anomalies()`
- Added `list_available_charts()` for dynamic API discovery
- Made all thresholds configurable via constructor parameters
- Wrote self-evaluation document with honest assessment

## Phase 5: MCP Server + Full Agent-Native (02:15-02:30 UTC)

Built MCP server with 7 tools (v0.3.0):
- `rc_list_charts` — dynamic discovery
- `rc_get_overview` — current metrics
- `rc_get_chart` — query any chart
- `rc_analyze_health` — full analysis with configurable thresholds
- `rc_calc_trend` — atomic trend primitive
- `rc_detect_anomalies` — atomic anomaly primitive
- `rc_generate_report` — multi-format report generation

Added `describe()` for self-describing capability manifest.
All tools tested against live Dark Noise API.

## Phase 6: Video Production (02:31-02:43 UTC)

- Generated narration via ElevenLabs TTS (79 seconds, multilingual v2)
- Generated 6 key frame images via OpenAI gpt-image-1 (1536x1024, high quality)
- Applied Ken Burns effect to each frame via ffmpeg
- Composited 6 scenes with narration overlay
- Final video: 1920x1080, h264, 30fps, 79s, 11.4MB
- Passed automated quality gate (resolution, fps, duration, codec checks)

## Phase 7: Final Audit + Polish (02:43-02:50 UTC)

- Fixed incorrect GitHub repo URLs in blog post and social posts
- Rewrote CLI for zero-dependency stdlib (was using click/rich which aren't installed)
- Added retry with backoff for API rate limits
- Verified all deliverables against assignment requirements line-by-line
- Tested CLI against live API: overview, health, chart, discover, report

---

## Key Decisions

| Decision | Reasoning |
|----------|-----------|
| Python library over web app | Most useful for devs AND agents. No hosting needed. |
| Zero dependencies (stdlib only) | Frictionless adoption. No pip dependency hell. |
| Health score (0-100) over raw data | Developers need decisions, not dashboards. |
| Agent-native architecture | MCP server, dynamic discovery, configurable thresholds, atomic primitives. |
| Open source (MIT) | Community tools compound. Proprietary demos die. |
| Self-evaluation included | Shows the loop: build → evaluate → improve. |
| ElevenLabs + gpt-image-1 + ffmpeg for video | Full autonomous production pipeline. No human intervention. |

## Tradeoffs

| Tradeoff | Choice | Why |
|----------|--------|-----|
| Click/Rich CLI vs stdlib | stdlib | Zero deps wins over pretty output |
| Full cohort analysis vs basic health | Basic health | Ship working v1, iterate on v2 |
| Test all 21 chart types vs test core 5 | Core 5 | Rate limits + time. Core charts cover 90% of use cases. |
| Single video vs multi-format | Single MP4 | One solid video > multiple mediocre ones |

## What I'd Do Differently With More Time

1. Test all 21 chart types and document schema differences
2. Add cohort analysis (the cohort_explorer endpoint)
3. Build a web dashboard that auto-refreshes
4. Create per-chart analysis primitives (revenue-specific, churn-specific)
5. Add scheduling for daily health reports
6. Generate social media image assets (OG cards, screenshots)
7. Record actual screen capture of the CLI in action (not just generated frames)
