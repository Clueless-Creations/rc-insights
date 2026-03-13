# rc-insights Self-Evaluation Against Agent-Native Principles

## Parity Assessment

| User Dashboard Action | rc-insights Agent Method | Status |
|---|---|---|
| View overview metrics | client.get_overview() | ✅ Full parity |
| View any chart | client.get_chart(name, ...) | ✅ Full parity |
| Change date range | start_date/end_date params | ✅ Full parity |
| Change resolution | resolution param | ✅ Full parity |
| Segment by dimension | segment_by param | ⚠️ Partial — param exists but not tested against all dimensions |
| Export data | report.save() (HTML/MD/JSON) | ✅ Parity via different format |
| Compare metrics side-by-side | get_multiple_charts() | ✅ |
| View cohort explorer | get_chart("cohort_explorer") | ⚠️ Untested — schema may differ from standard charts |
| Apply filters (country/store/product) | Not implemented | ❌ Missing — dashboard supports these |

**Parity score: 7/9 — Good but incomplete.** Filters and cohort explorer need verification.

## Granularity Assessment

| Tool/Method | Atomic? | Issue |
|---|---|---|
| ChartsClient.get_chart() | ✅ Yes — single chart, single call | |
| ChartsClient.get_overview() | ✅ Yes — single action | |
| ChartsClient.get_health_charts() | ⚠️ Convenience, not atomic | Bundles 5 API calls. Fine as a shortcut but should NOT replace individual access. |
| ChartsClient.discover_project_id() | ✅ Yes | |
| InsightsAnalyzer.analyze_health() | ❌ Workflow-shaped | Bundles analysis logic. An agent should be able to call trend analysis and anomaly detection separately. |
| ReportGenerator.save() | ⚠️ Bundles formats | Should allow generating one format at a time without the others. |

**Granularity score: Moderate.** The client layer is properly atomic. The analyzer is a workflow-shaped tool — it bundles judgment (what counts as "critical"? what thresholds?) into code instead of leaving it to the agent's prompt. This is the biggest violation.

### What Should Change

The analyzer should expose atomic primitives:
- calc_trend(values, window) — just the math
- detect_anomalies(values, threshold) — just the detection
- score_health(insights) — just the scoring

Then analyze_health() becomes a convenience that calls these, but agents can compose their own analysis with different thresholds, different logic, different judgment.

## Composability Assessment

**Can a new feature be added with just a new prompt?**

- "Pull MRR and churn, tell me if I should worry" → ✅ Agent can compose get_chart + get_chart + judgment
- "Compare revenue by country and recommend which market to focus on" → ⚠️ Needs segment_by to work, plus agent judgment. Partially composable.
- "Track my MRR daily and alert me if it drops 10%" → ❌ No scheduling, no state persistence, no alerting primitive. Would need code changes.

**Composability score: Moderate.** Good for single-session analysis. Poor for anything requiring persistence or scheduling.

## Emergent Capability Assessment

**Can the agent do things I didn't design for?**

- Custom analysis with different thresholds? → ❌ Not without code changes (thresholds are hardcoded in analyzer)
- Correlate charts against each other? → ⚠️ Agent can pull multiple charts and reason, but no correlation primitive
- Generate a board deck from the data? → ✅ Agent can pull data + use report templates + judgment
- Compare this month vs last month? → ✅ Agent calls get_chart twice with different date ranges

**Emergent score: Moderate.** The hardcoded thresholds in the analyzer are the main blocker. If those were configurable or exposed as primitives, emergent capability would be much higher.

## Completion Signals

- get_chart() returns a ChartResponse with data or raises RuntimeError → ✅ Clear success/failure
- analyze_health() returns AnalysisReport with health_score → ✅ Clear result
- No explicit should_continue signal → ❌ Missing
- No partial completion tracking → ❌ Missing

**Completion score: Weak.** Works for single calls but doesn't support agent loops well.

## Dynamic Capability Discovery

- Chart names are hardcoded as a Python Enum → ❌ Static mapping
- The API returns the valid chart names in error messages → Opportunity: could build a list_available_charts() that discovers dynamically
- Overview metrics have IDs but these aren't discoverable → ❌ Static

**Discovery score: Poor.** This is the easiest fix with the highest impact. One new method solves it.

## Context Injection

- README has usage examples → ✅ Good for human context
- No agent-specific context.md or system prompt snippet → ❌ Missing
- JSON output format documented → ✅ Agent can parse
- No MCP tool definition → ❌ Would make rc-insights directly usable by any agent runtime

**Context score: Moderate.** Works for Python-native agents. Not discoverable by MCP-based agents.

---

## Priority Fixes

### P0 (Before submission if time allows)
1. **Add list_available_charts()** — dynamic discovery from API error response or hardcoded with a refresh mechanism
2. **Expose analyzer primitives** — calc_trend(), detect_anomalies() as public methods (they already exist as _trend and _anomalies, just make them public)
3. **Make thresholds configurable** — analyzer should accept threshold params, not hardcode them

### P1 (Next iteration)
4. **Add filter support** — country, store, product filters on get_chart()
5. **Add explicit completion signals** — ToolResult-style returns with should_continue
6. **Add MCP tool definition** — so any agent runtime can discover and use rc-insights
7. **Test cohort_explorer endpoint** — verify schema compatibility

### P2 (Future)
8. **Scheduling/persistence layer** — for daily monitoring use cases
9. **Correlation primitives** — cross-chart analysis tools
10. **Agent context snippet** — ready-to-paste system prompt block describing capabilities

---

## Content Package Evaluation

### Blog Post
- ✅ Opens with developer problem, not product pitch
- ✅ Real code examples (tested against live API)
- ✅ Architecture diagram
- ✅ Over 1,500 words
- ⚠️ Could use more internal links to RC resources
- ⚠️ Health score section is good but could include a real Dark Noise example with actual numbers from the API call
- ❌ Section headers could be more RC-style descriptive ("Two billing systems, zero interoperability" style)

### Social Posts
- ✅ Each has a different angle
- ✅ AI disclosure in every post
- ✅ CTAs are specific (pip install command)
- ⚠️ No actual images generated yet — need OG cards and screenshots
- ⚠️ Post 3 (agent angle) could be more grounded with a specific example instead of a prediction

### Growth Campaign
- ✅ Five communities identified with specific post copy
- ✅ Budget allocated with rationale
- ✅ Measurement plan with targets
- ⚠️ Targets are aspirational without baseline data — should acknowledge this
- ⚠️ No A/B testing plan for the social posts themselves

### Video
- ✅ Script written
- ✅ Narration generated
- ❌ Not yet composited — needs ffmpeg
- ⚠️ Should show REAL Dark Noise data in the demo, not generic examples

### Process Log
- ✅ Timestamped
- ✅ Decisions documented with rationale
- ⚠️ Missing: what I tried that didn't work (the sandbox limitations, endpoint discovery attempts)
- ⚠️ Missing: time spent per phase (only approximate)

---

## Overall Assessment

**What's strong:** The tool works against real data. Zero dependencies. Clean API abstraction. Content package is complete. Campaign is specific.

**What's weak by agent-native standards:** Analyzer bundles judgment into code instead of exposing primitives. Static capability mapping. No MCP integration. No explicit completion signals. Thresholds are hardcoded.

**What's weak by RC editorial standards:** Blog post headers could be more descriptive. Could use more real Dark Noise numbers throughout. Internal linking to RC resources is light. No actual visual assets generated yet.

**Honest grade: B-.** Functional and complete, but not yet excellent. The agent-native gaps are the most significant because they limit how other agents (and Katire itself) can use the tool.

---

*This evaluation will be applied to every future deliverable before publication.*
