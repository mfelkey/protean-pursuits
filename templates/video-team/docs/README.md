# Video Team — Template

Part of the Protean Pursuits multi-agent platform.

---

## What this team does

The Video Team produces complete video production packages — from brief through compliance clearance — for any Protean Pursuits project. It never publishes autonomously. Every deliverable requires human approval before any asset is released or any API call that costs money is made.

**Formats supported:** Short-form social (TikTok, Reels, Shorts), long-form (YouTube, website), avatar/spokesperson, product demo, animated explainer, voiceover-only.

---

## Agents

| Agent | File | Tier | Produces |
|---|---|---|---|
| Video Orchestrator | `agents/orchestrator/orchestrator.py` | T1 | Sequences crew, synthesises, fires HITL gates |
| Script Writer | `agents/script/script_writer.py` | T1 | Script Package (copy + timestamps + compliance checklist) |
| Visual Director | `agents/visual/visual_director.py` | T1 | Visual Direction Brief (shot types, motion, AI prompt strings) |
| Audio Producer | `agents/audio/audio_producer.py` | T1 | Audio Production Brief (music prompts, TTS direction, SFX cue sheet) |
| Avatar Producer | `agents/avatar/avatar_producer.py` | T1 | Avatar Production Brief (HeyGen/Synthesia execution params) |
| Tool Intelligence Analyst | `agents/tool_intelligence/tool_analyst.py` | T1 | Tool Recommendation Report (scored rankings, API signatures) |
| Compliance Reviewer | `agents/compliance/compliance_reviewer.py` | T1 | Compliance Report (PASS / CONDITIONAL / FAIL) |
| API Production Engineer | `agents/production/api_engineer.py` | T2 | Assembly Manifest (executes approved APIs, saves raw assets) |

---

## Run modes

| Mode | Pipeline | HITL gates |
|---|---|---|
| `BRIEF_ONLY` | Tool Analyst → Script → Visual → Audio | TOOL_SELECTION + SCRIPT_REVIEW |
| `SHORT_FORM` | Full pipeline, <60s social | TOOL_SELECTION + SCRIPT_REVIEW + VIDEO_FINAL |
| `LONG_FORM` | Full pipeline, 2–10min | TOOL_SELECTION + SCRIPT_REVIEW + VIDEO_FINAL |
| `AVATAR` | Full pipeline, avatar foregrounded | TOOL_SELECTION + SCRIPT_REVIEW + VIDEO_FINAL |
| `DEMO` | Script → Audio → API → Compliance | SCRIPT_REVIEW + VIDEO_FINAL |
| `EXPLAINER` | Full pipeline, animated | TOOL_SELECTION + SCRIPT_REVIEW + VIDEO_FINAL |
| `VOICEOVER` | Script → Audio → API → Compliance | SCRIPT_REVIEW + VIDEO_FINAL |
| `FULL` | BRIEF_ONLY → SHORT_FORM → LONG_FORM → AVATAR | All gates |

`DEMO` and `VOICEOVER` skip visual generation. `AVATAR` substitutes `avatar_producer` for `visual_director`.

---

## HITL gates

| Gate | When | What to review |
|---|---|---|
| `VIDEO_TOOL_SELECTION` | After Tool Analyst | Is the tool stack appropriate? Do you have the API keys configured? |
| `SCRIPT_REVIEW` | After Script Writer | Is the script accurate, on-brand, compliant? Review COMPLIANCE CHECKLIST at the bottom. |
| `VIDEO_FINAL` | After Compliance Reviewer | Is the full package approved? Review COR rating (PASS / CONDITIONAL / FAIL). |

**No API call that costs money is made without passing SCRIPT_REVIEW.**

---

## Quickstart

```bash
# From repo root
cd ~/projects/protean-pursuits

# Run via pp_flow.py
python flows/pp_flow.py --team video --mode BRIEF_ONLY \
    --task "60s TikTok ad for ParallaxEdge sports betting app launch" \
    --project parallaxedge --save

# Run a single agent directly
python flows/pp_flow.py --team video --agent script_writer \
    --task "Write 60s TikTok script for ParallaxEdge" \
    --project parallaxedge --save

# List all modes and agents
python flows/pp_flow.py --team video --list-modes
```

---

## Configuration

Copy `.env.template` to `.env` and fill in the keys you have access to:

```bash
cp config/.env.template config/.env
```

The Tool Intelligence Analyst reads available keys at runtime and recommends the best tool stack from what's configured. You don't need all keys — the agent adapts to what's available.

**Minimum for `BRIEF_ONLY` mode:** No API keys required (no external calls).
**Minimum for `SHORT_FORM` / `LONG_FORM`:** At least one video gen API key + one audio API key.
**Minimum for `AVATAR`:** At least one avatar API key (HeyGen, Synthesia, or D-ID).

See `config/.env.template` for the full list.

---

## Output structure

```
output/
  briefs/        Script packages, visual direction briefs, audio briefs, avatar briefs
  compliance/    Compliance reports (PASS / CONDITIONAL / FAIL)
  renders/       Raw asset manifests, assembly manifests from API Engineer
```

---

## File structure

```
templates/video-team/
  agents/
    orchestrator/   Video Orchestrator + base_agent factory
    script/         Script Writer
    visual/         Visual Director
    audio/          Audio Producer
    avatar/         Avatar Producer
    tool_intelligence/  Tool Intelligence Analyst
    compliance/     Compliance Reviewer
    production/     API Production Engineer
  config/
    .env.template   All supported env vars with comments
    .env            Your local keys (gitignored)
    config.py       Centralised config loader (import cfg from here)
  docs/
    README.md       This file
  flows/
    video_flow.py       Team orchestrator flow (8 modes)
    video_agent_flow.py Single-agent direct flow
  memory/
    tool_cache.json     Tool Intelligence Analyst delta cache
  output/
    briefs/
    compliance/
    renders/
```
