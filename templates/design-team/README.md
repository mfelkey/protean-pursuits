# design-team — Template

> **This is a Protean Pursuits team template.**
> Instantiated by `scripts/refresh_templates.py` from `teams/design-team/`.
> Last refreshed: 2026-03-23 21:18 UTC
> Replace all `PROJECT_NAME_PLACEHOLDER` and `PROJ-TEMPLATE` tokens.

---

# Protean Pursuits — Design Team

**Version:** 1.0 | **Tooling:** Tool-agnostic (precise specs, any tool)

Portfolio-wide design — serves Dev, Marketing, Strategy, Legal, and all other teams.

## 8 Agents
| Agent | Output |
|---|---|
| UX Research & Discovery | Personas, journey maps, opportunity frameworks |
| Wireframing & Prototyping | Annotated wireframes, interaction flows, prototype scripts |
| UI Design & Component Library | Component specs with all tokens, states, variants |
| Brand & Visual Identity | Colour palettes, typography, logo guidelines, brand docs |
| Motion & Animation | Duration scales, easing curves, component animation specs |
| Design System Management | Token architecture, component catalogue, theming guides |
| Accessibility (WCAG) | WCAG 2.1 AA audits, remediation specs, VPAT documents |
| Usability | Heuristic evaluations, cognitive walkthroughs, usability test plans |

## Run Modes
```bash
# Single agent brief
python flows/design_flow.py --mode brief --agent ui_design --name "Signal Card" --project-id PROJ-TEMPLATE

# UX sprint (research → wireframe → usability)
python flows/design_flow.py --mode ux_sprint --name "Bet Tracker Feature" --project-id PROJ-TEMPLATE

# Brand build (identity + system + motion + accessibility)
python flows/design_flow.py --mode brand_build --name "PROJECT_NAME_PLACEHOLDER Brand System"

# Accessibility + usability audit
python flows/design_flow.py --mode audit --name "PROJECT_NAME_PLACEHOLDER Accessibility Audit"
```

All outputs require human review before handoff to implementation teams.
