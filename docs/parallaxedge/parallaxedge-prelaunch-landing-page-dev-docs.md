# ParallaxEdge — Pre-Launch Landing Page
## Developer Documentation v1.0

> **Status:** Mockup approved. Ready for development.  
> **Last updated:** March 2026  
> **Audience:** Frontend development team  

---

## Table of Contents

1. [Overview](#1-overview)
2. [Page Structure](#2-page-structure)
3. [Design Tokens](#3-design-tokens)
4. [Component Specifications](#4-component-specifications)
5. [Copy & Content](#5-copy--content)
6. [Interactions & Behaviour](#6-interactions--behaviour)
7. [Age Gate & Form Logic](#7-age-gate--form-logic)
8. [Known Issues & Environment Notes](#8-known-issues--environment-notes)

---

## 1. Overview

This document covers the full specification for the ParallaxEdge pre-launch landing page. The page has one primary goal: collect email sign-ups from prospective users ahead of the World Cup 2026 launch on 11 June 2026.

**Secondary goals:**
- Communicate the product proposition clearly
- Preview the signal card UI to build anticipation
- Signal the sports coverage roadmap (Football, NFL, NBA)
- Gate sign-ups behind an age declaration to comply with betting industry regulations

**Page URL:** `/` (root, pre-launch only — to be replaced by the full product landing page at launch)

---

## 2. Page Structure

The page is composed of seven sections in the following order:

```
┌─────────────────────────┐
│ 1. Navigation            │
├─────────────────────────┤
│ 2. Hero                  │
│    — Eyebrow             │
│    — Headline            │
│    — Sub-copy            │
│    — Countdown timer     │
│    — Email capture form  │
│    — Age gate checkbox   │
│    — Incentive copy      │
│    — Social links        │
├─────────────────────────┤
│ 3. Sports coverage strip │
├─────────────────────────┤
│ 4. Signal card preview   │
├─────────────────────────┤
│ 5. Footer                │
└─────────────────────────┘
```

**Layout:** Single-column, full-width. Maximum content width should be constrained to `1200px` centred on wide viewports. The signal card grid has its own internal max-width of `860px`.

**Background:** The page background is `#0A1628` (Deep Navy) for all sections except the signal preview section, which uses `#112038` (Navy Surface).

---

## 3. Design Tokens

### 3.1 Colour Palette

Define these as CSS custom properties at the `:root` level.

```css
:root {
  /* Backgrounds */
  --color-navy:        #0A1628;  /* Page background */
  --color-navy-2:      #112038;  /* Surface / card background */
  --color-navy-3:      #1A2F50;  /* Elevated card / dashboard surface */

  /* Text */
  --color-white:       #F0F4FA;  /* Primary text */
  --color-white-2:     #C8D4E8;  /* Secondary text */
  --color-white-3:     #94A8C4;  /* Muted / metadata text */

  /* Accent */
  --color-teal:        #00D4B4;  /* Primary accent — high confidence, CTAs */
  --color-teal-2:      #00B89C;  /* Teal hover state */
  --color-amber:       #F5A623;  /* Secondary accent — medium confidence, warnings */
  --color-amber-2:     #E09015;  /* Amber hover state */
}
```

**Signal colour system — use consistently across all signal-related UI:**

| Colour | Hex | Meaning |
|--------|-----|---------|
| Teal | `#00D4B4` | High-confidence edge detected |
| Amber | `#F5A623` | Medium-confidence signal, monitor |
| Muted white-3 | `#94A8C4` | Inactive, offline, insufficient data |

### 3.2 Typography

Import from Google Fonts:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
```

**Typeface roles:**

| Typeface | Variable | Usage |
|----------|----------|-------|
| DM Serif Display | `--font-display` | Headlines, hero text, section titles, stat numbers |
| IBM Plex Mono | `--font-mono` | Data, labels, badges, metadata, button text, eyebrows |
| DM Sans | `--font-body` | Body copy, sub-copy, UI text |

**Type scale:**

| Element | Font | Size | Weight | Colour |
|---------|------|------|--------|--------|
| Hero h1 | DM Serif Display | 62px | 400 | `--color-white` |
| Section title | DM Serif Display | 34–40px | 400 | `--color-white` |
| Stat number | DM Serif Display | 40px | 400 | `--color-white` |
| Eyebrow | IBM Plex Mono | 11px | 400 | `--color-teal` |
| Button | IBM Plex Mono | 13px | 500 | `#05111F` on teal bg |
| Badge | IBM Plex Mono | 9–10px | 400 | Contextual (teal/amber) |
| Body / sub-copy | DM Sans | 15–17px | 300 | `--color-white-2` |
| Metadata / labels | IBM Plex Mono | 10–11px | 400 | `--color-white-3` |

**Letter spacing:**
- Eyebrows and labels: `2–3px`
- Buttons: `0.5px`
- Body copy: default (`0`)

---

## 4. Component Specifications

### 4.1 Navigation

**Behaviour:** Sticky. Stays at the top of the viewport on scroll.  
**Background:** `rgba(10, 22, 40, 0.95)` with `backdrop-filter: blur(12px)` for a frosted glass effect over the page content.  
**Border:** `1px solid rgba(200, 212, 232, 0.1)` on the bottom edge.  
**Height:** `~62px`  
**Padding:** `20px 48px`

**Left:** Logo — "Parallax" in `--color-white`, "Edge" in `--color-teal`. Use `DM Serif Display`, 22px.  
**Right:** Single text label — "COMING SUMMER 2026" in `IBM Plex Mono`, 11px, `--color-white-3`, letter-spacing `1.5px`. No links or navigation items on the pre-launch page.

---

### 4.2 Hero Section

**Background:** Transparent — inherits page navy. Two decorative radial glow elements (teal, low opacity) positioned top-left and top-right. A subtle grid overlay using CSS `background-image` with `linear-gradient` lines at `4% opacity`.

**Grid overlay CSS:**
```css
background-image:
  linear-gradient(rgba(0, 212, 180, 0.04) 1px, transparent 1px),
  linear-gradient(90deg, rgba(0, 212, 180, 0.04) 1px, transparent 1px);
background-size: 48px 48px;
```

**Padding:** `64px 48px 0`  
**Text alignment:** Centred

**Eyebrow:** "AI-POWERED BETTING INTELLIGENCE" — IBM Plex Mono, 11px, `--color-teal`, letter-spacing `2.5px`, margin-bottom `24px`.

**Headline:** Two lines. "Discover opportunities / most of the *market misses.*"
- Font: DM Serif Display, 62px, letter-spacing `-2px`, line-height `1.05`
- "Discover opportunities most of the" — `--color-white`
- "market misses." — `--color-teal`, italic

**Sub-copy:** DM Sans, 16px, weight 300, `--color-white-2`, line-height `1.75`, max-width `480px`, centred. Margin-bottom `48px`.

---

### 4.3 Countdown Timer

A live countdown to the FIFA World Cup 2026 opening match: **11 June 2026, 18:00 UTC**.

**Layout:** Four blocks in a horizontal row, separated by colon dividers.

**Each block:**
- Background: `#112038`
- Border: `1px solid rgba(200, 212, 232, 0.1)`
- Border radius: `8px`
- Padding: `16px 20px`
- Min-width: `80px`
- Number: DM Serif Display, 40px, `--color-white`, letter-spacing `-1px`
- Label: IBM Plex Mono, 9px, `--color-white-3`, letter-spacing `2px`, margin-top `6px`

**Separator colons:** DM Serif Display, 36px, `--color-teal`, opacity `0.5`. Vertically centred, offset upward slightly to optically align with the numbers.

**Event label below timer:** IBM Plex Mono, 10px, `--color-white-3`, letter-spacing `1.5px`, centred. "FIFA WORLD CUP 2026" highlighted in `--color-amber`.

**JavaScript — countdown logic:**
```javascript
const launch = new Date('2026-06-11T18:00:00Z');

function tick() {
  const now = new Date();
  const diff = launch - now;

  if (diff <= 0) {
    ['days', 'hours', 'mins', 'secs'].forEach(unit => {
      document.getElementById(`cd-${unit}`).textContent = '00';
    });
    return;
  }

  const d = Math.floor(diff / 86400000);
  const h = Math.floor((diff % 86400000) / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);

  document.getElementById('cd-days').textContent  = String(d).padStart(2, '0');
  document.getElementById('cd-hours').textContent = String(h).padStart(2, '0');
  document.getElementById('cd-mins').textContent  = String(m).padStart(2, '0');
  document.getElementById('cd-secs').textContent  = String(s).padStart(2, '0');
}

tick();
setInterval(tick, 1000);
```

> **Note:** When the countdown reaches zero, all values display `00`. Consider adding a "We're live" state that replaces the timer with a CTA to enter the product.

---

### 4.4 Email Capture Form

The form is composed of a text input and a submit button in a single horizontal unit, bordered by a teal outline.

**Wrapper:** `max-width: 480px`, centred. Border: `1px solid rgba(0, 212, 180, 0.35)`, border-radius `5px`, overflow `hidden`.

**Email input:**
- Background: `rgba(17, 32, 56, 0.9)`
- Text colour: `--color-white`
- Placeholder colour: `--color-white-3`
- Font: DM Sans, 14px
- Padding: `15px 18px`
- No border (border is on the wrapper)
- `outline: none` — use custom focus state if needed for accessibility

**Submit button:**
- Background: `--color-teal` when enabled; `rgba(0, 212, 180, 0.3)` when disabled
- Text colour: `#05111F` (very dark navy — **not black, not white**)
- Font: IBM Plex Mono, 13px, weight 500, letter-spacing `0.5px`
- Padding: `15px 24px`
- Label: "GET EARLY ACCESS"
- `white-space: nowrap` — prevents label from wrapping on narrow viewports
- Hover state: `--color-teal-2`
- **Disabled by default.** Enabled only when the age gate checkbox is checked (see Section 7).

> ⚠️ **Button text colour note:** The button text must be `#05111F` — a very dark near-black navy — against the teal background. Do not use `#000000` (pure black) or inherit from parent elements. Set this explicitly on the button element. See Section 8 for context on why this is called out.

---

### 4.5 Incentive Copy

Single line of small text below the age gate, centred.

**Copy:** "First 1,000 confirmed sign-ups get every AI signal, every match, free for the entire Group Stage"  
**Font:** IBM Plex Mono, 10px, `--color-white-3`, letter-spacing `0.5px`  
**"every AI signal, every match"** — no special styling needed, but consider bolding or teal highlight if the design needs more emphasis at this size.

---

### 4.6 Social Links

Three horizontally arranged pill-style links. Displayed below the incentive copy, above the sports coverage strip.

**Each link:**
- Background: `#112038`
- Border: `1px solid rgba(200, 212, 232, 0.1)`
- Border-radius: `5px`
- Padding: `10px 18px`
- Font: IBM Plex Mono, 12px, `--color-white-2`, letter-spacing `0.5px`
- Icon: 16×16px SVG, `fill: currentColor`
- Hover: border-color transitions to `rgba(0, 212, 180, 0.35)`, text to `--color-white`
- Gap between icon and label: `8px`

**Links (update hrefs before launch):**
- Follow on X → `https://x.com/parallaxedge`
- Follow on Instagram → `https://instagram.com/parallaxedge`
- Watch on YouTube → `https://youtube.com/@parallaxedge`

---

### 4.7 Sports Coverage Strip

A row of sport pills communicating the coverage roadmap. Positioned between the hero social links and the signal preview section.

**Section padding:** `0 48px 72px`  
**Label above pills:** "SPORTS COVERAGE" — IBM Plex Mono, 10px, letter-spacing `3px`, `--color-white-3`, centred.

**Each pill:**
- Background: `#112038`
- Border: `1px solid rgba(200, 212, 232, 0.1)`
- Border-radius: `6px`
- Padding: `12px 20px`
- Hover: border-color `rgba(0, 212, 180, 0.25)`
- Layout: flex row, icon + text block, gap `10px`

**Sport name:** DM Sans, 13px, weight 500, `--color-white`  
**Status label:** IBM Plex Mono, 10px, letter-spacing `0.5px`

**Status label colours:**
- Teal (`--color-teal`): Launching / live
- Amber (`--color-amber`): Coming soon within the year
- Muted (`--color-white-3`): Further out / TBD

**Four pills — copy and status:**

| Sport | Icon | Status label | Colour |
|-------|------|-------------|--------|
| Football | ⚽ | Launching June 2026 | Teal |
| NFL | 🏈 | Season starts Sep 2026 | Amber |
| NBA | 🏀 | Season starts Oct 2026 | Muted |
| More sports | ＋ | Coming soon | Muted |

> **Note on icons:** The emoji icons work for the mockup. For production, replace with custom SVG sport icons to maintain the technical brand aesthetic and ensure consistent rendering across platforms.

---

### 4.8 Signal Card Preview

**Section background:** `#112038`  
**Border:** `1px solid rgba(200, 212, 232, 0.08)` top and bottom  
**Padding:** `56px 48px`

**Section header:**
- Label: "SIGNAL PREVIEW" — IBM Plex Mono, 10px, `--color-teal`, letter-spacing `3px`, centred
- Title: "What the model sees." — DM Serif Display, 34px, `--color-white`, centred
- Sub-label: "Live intelligence cards · Available at launch" — IBM Plex Mono, 14px, `--color-white-3`, centred

**Card grid:** 3 columns, `gap: 16px`, max-width `860px`, centred.

**Each signal card:**
- Background: `#1A2F50`
- Border: `1px solid rgba(200, 212, 232, 0.09)`
- Border-radius: `8px`
- Padding: `20px`
- Top accent bar: `2px` full-width strip at the very top of the card (achieved with `::before` pseudo-element or a top border)
  - High confidence: gradient `#00B89C → #00D4B4`
  - Medium confidence: gradient `#E09015 → #F5A623`

**Card internal layout (top to bottom):**

1. **Match header row** — flex, space-between
   - Left: Match name (DM Sans, 13px, weight 500, `--color-white`) + date/stage below (IBM Plex Mono, 11px, `--color-white-3`)
   - Right: Confidence badge

2. **Confidence badge:**
   - High: background `rgba(0, 212, 180, 0.15)`, border `1px solid rgba(0, 212, 180, 0.3)`, text `--color-teal`, label "HIGH CONF"
   - Medium: background `rgba(245, 166, 35, 0.12)`, border `1px solid rgba(245, 166, 35, 0.3)`, text `--color-amber`, label "MED CONF"
   - Font: IBM Plex Mono, 9px, letter-spacing `1px`, border-radius `2px`, padding `3px 8px`

3. **Edge value:** IBM Plex Mono, 32px, weight 500 — teal for high, amber for medium

4. **Edge type label:** IBM Plex Mono, 10px, `--color-white-3`, letter-spacing `0.5px` — e.g. "BRAZIL WIN · PRE-MATCH EDGE"

5. **Confidence bar:**
   - Label row: "CONFIDENCE" left, percentage right — IBM Plex Mono, 10px, `--color-white-3`
   - Bar track: `3px` height, `rgba(200, 212, 232, 0.1)` background, border-radius `2px`
   - Bar fill: gradient — teal for high, amber for medium — width set by confidence percentage

6. **Signal list:** Three items, each with a 5×5px dot indicator and label text (IBM Plex Mono, 10px, `--color-white-3`)
   - Active signal dot: `--color-teal`
   - Inactive/offline dot: `rgba(200, 212, 232, 0.25)`

**Third card — locked state:**
The third card (England vs Portugal) is blurred and overlaid with a lock message. This communicates that more signals are available after sign-up.

- Apply `filter: blur(3px)` to the card
- Set `pointer-events: none` and `user-select: none`
- Overlay: absolutely positioned, centred, containing a lock icon (◎) and "UNLOCKS AT LAUNCH" label (IBM Plex Mono, 11px, `--color-white-2`)

---

### 4.9 Footer

**Padding:** `24px 48px`  
**Border:** `1px solid rgba(200, 212, 232, 0.07)` top  
**Layout:** Flex row, space-between, vertically centred

**Left:** Logo — "Parallax" in `--color-white-2`, "Edge" in `--color-teal`. DM Serif Display, 15px.  
**Centre:** Three text links — Privacy, Terms, Responsible Gambling. DM Sans, 11px, `--color-white-3`. Hover: `--color-white-2`.  
**Right:** "© 2026 PARALLAXEDGE" — IBM Plex Mono, 10px, `--color-white-3`, letter-spacing `1px`.

> ⚠️ All three footer links must point to live, legally reviewed pages before the site goes live. Responsible Gambling in particular must link to a compliant page with jurisdiction-appropriate resources.

---

## 5. Copy & Content

All copy is final and approved unless marked otherwise. Do not alter wording without brand approval.

### 5.1 Navigation
- Logo: **ParallaxEdge** (Parallax + Edge, no space)
- Nav label: `COMING SUMMER 2026`

### 5.2 Hero
- Eyebrow: `AI-POWERED BETTING INTELLIGENCE`
- Headline: `Discover opportunities most of the market misses.`
  - Italic teal: `market misses.`
- Sub-copy: `AI-powered signals that find value before the market does. Built for the World Cup. Built for every bettor.`
- Countdown event label: `UNTIL FIFA WORLD CUP 2026 OPENING MATCH · 11 JUNE 2026`
- Button: `GET EARLY ACCESS`
- Age gate: `I confirm I am 18 years of age or older and agree to the Terms of Service and Privacy Policy. ParallaxEdge is a betting intelligence tool intended for adults in jurisdictions where sports betting is legal.`
- Incentive: `First 1,000 confirmed sign-ups get every AI signal, every match, free for the entire Group Stage`

> ⚠️ **Legal review required:** The age gate copy and footer link destinations must be reviewed and approved by legal counsel before launch.

### 5.3 Signal Preview
- Section label: `SIGNAL PREVIEW`
- Title: `What the model sees.`
- Sub-label: `Live intelligence cards · Available at launch`
- Locked card overlay: `UNLOCKS AT LAUNCH`

### 5.4 Signal Card Data (mockup only — not real model output)

| Field | Card 1 | Card 2 | Card 3 (locked) |
|-------|--------|--------|-----------------|
| Match | Brazil vs Argentina | France vs Germany | England vs Portugal |
| Stage | Group Stage · 14 Jun | Group Stage · 17 Jun | Group Stage · 20 Jun |
| Confidence | HIGH CONF | MED CONF | HIGH CONF |
| Edge | +7.4% | +3.1% | +5.8% |
| Type | BRAZIL WIN · PRE-MATCH EDGE | DRAW · LIVE ODDS SHIFT | OVER 2.5 · IN-PLAY EDGE |
| Confidence % | 84% | 52% | 71% |
| Signal 1 | xG Differential +1.34 | Formation Advantage +0.61 | xG Differential +1.12 |
| Signal 2 | Market Drift Index +0.82 | Weather Adjustment (offline) | Market Drift Index +0.55 |
| Signal 3 | Fatigue Model –0.21 | Referee Bias +0.14 | Press Intensity +0.38 |

> ⚠️ **This is placeholder data.** Replace with real model output before launch, or confirm with the product team whether static demo data is acceptable at go-live.

---

## 6. Interactions & Behaviour

### 6.1 Countdown Timer
- Updates every 1 second via `setInterval`
- All units display as zero-padded two-digit strings (e.g. `03`, not `3`)
- When diff reaches zero or below, all units display `00`
- Target: `2026-06-11T18:00:00Z` (UTC — do not use local time)

### 6.2 Button Hover States
- Teal CTA: background transitions from `#00D4B4` to `#00B89C` on hover
- Social link pills: border-color transitions to `rgba(0, 212, 180, 0.35)`, text to `--color-white`
- Sport coverage pills: border-color transitions to `rgba(0, 212, 180, 0.25)`
- All transitions: `0.2s ease`

### 6.3 Age Gate → Button Unlock
See Section 7 for full logic. In summary: the submit button is disabled until the age gate checkbox is checked. Checking it enables the button and transitions it to the active teal state.

### 6.4 Nav Scroll Behaviour
The navigation is sticky (`position: sticky; top: 0`). The frosted glass background (`backdrop-filter: blur`) ensures it remains legible over the hero grid and glow effects as the user scrolls.

### 6.5 Post-Submission State
The mockup does not define a post-submission state. Before launch, define and implement:
- Success state: confirmation message replacing the form, e.g. "You're on the list."
- Error state: inline validation for invalid email format
- Full state: message if the 1,000 sign-up cap has been reached

---

## 7. Age Gate & Form Logic

### 7.1 Purpose
The age gate ensures that users self-declare they are 18 or older before submitting their email. This is a minimum compliance requirement for a betting-adjacent product. It also serves as implicit acceptance of the Terms of Service and Privacy Policy.

> ⚠️ **Important:** A self-declaration checkbox is the minimum viable approach shown in the mockup. Depending on the jurisdictions ParallaxEdge operates in, legal counsel may require a date-of-birth field or third-party age verification at account activation. Confirm the required approach with your legal team before development begins.

### 7.2 Default State
- Checkbox: unchecked
- Submit button: disabled
- Submit button background: `rgba(0, 212, 180, 0.3)` (dimmed teal)
- Submit button cursor: `not-allowed`

### 7.3 Checked State
- Checkbox: checked (teal fill, dark navy tick mark)
- Submit button: enabled
- Submit button background: `#00D4B4`
- Submit button cursor: `pointer`

### 7.4 Logic
```javascript
let ageConfirmed = false;

function toggleAge() {
  ageConfirmed = !ageConfirmed;

  const checkbox = document.getElementById('age-checkbox');
  const button = document.getElementById('submit-btn');

  if (ageConfirmed) {
    checkbox.classList.add('checked');
    button.disabled = false;
    button.style.background = '#00D4B4';
    button.style.cursor = 'pointer';
  } else {
    checkbox.classList.remove('checked');
    button.disabled = true;
    button.style.background = 'rgba(0, 212, 180, 0.3)';
    button.style.cursor = 'not-allowed';
  }
}
```

### 7.5 Validation Rules
Before the form can be submitted, both conditions must be true:
1. The email input contains a valid email address (use HTML5 `type="email"` as a baseline; add regex validation for production)
2. The age gate checkbox is checked

If either condition is false, the button must remain disabled or the form submission must be blocked.

### 7.6 Data Handling
- The email address and age confirmation timestamp must be stored securely
- Do not store the age declaration as a boolean only — log the timestamp of confirmation for audit purposes
- Confirm data storage and GDPR/privacy compliance requirements with your backend team

---

## 8. Known Issues & Environment Notes

### 8.1 Button Text Colour Override
**Issue:** In certain environments (notably the Claude.ai preview widget used during design), the host environment's CSS aggressively overrides button text colour, causing the "GET EARLY ACCESS" button label to appear black rather than the intended near-white (`#F0F4FA` / `#05111F` on teal).

**In production this will not be an issue** — you have full control over the CSS cascade in a standalone HTML file or framework component.

**Recommendation:** Set the button text colour explicitly on the element using both a CSS class and an inline style as a fallback:
```html
<button
  class="email-submit"
  style="color: #05111F;"
  id="submit-btn"
  disabled
>
  GET EARLY ACCESS
</button>
```

### 8.2 Emoji Icons in Sports Coverage Strip
The sport icons in the coverage pills (⚽ 🏈 🏀) are rendered as emoji in the mockup. Emoji rendering varies significantly across operating systems and browsers.

**Recommendation:** Replace with custom SVG icons before launch to ensure consistent rendering and to maintain the brand's technical aesthetic.

### 8.3 Google Fonts Loading
The page uses three Google Fonts families loaded via `@import`. On slow connections, this can cause a flash of unstyled text (FOUT).

**Recommendation:** Use `<link rel="preconnect">` and `<link rel="preload">` tags in the `<head>` to prioritise font loading. Consider self-hosting the fonts for production to eliminate the third-party dependency.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

### 8.4 Responsive Breakpoints
The mockup was designed and reviewed at desktop width. Responsive behaviour for tablet and mobile has not been specified.

**Recommendation:** Define breakpoints before development begins. Key elements that will need adaptation:
- Hero headline font size (62px will overflow on mobile)
- Countdown timer block sizing
- Signal card grid (3 columns → 1 column on mobile)
- Social link pills (may need to stack vertically)
- Navigation (consider a simplified mobile nav)

### 8.5 Countdown Target Time
The countdown targets `2026-06-11T18:00:00Z`. Confirm the exact kickoff time and timezone with the product team as the World Cup schedule is confirmed closer to launch. Update the JavaScript constant if the time changes.

### 8.6 Sign-up Cap Logic
The incentive copy references "First 1,000 confirmed sign-ups." The page has no mechanism to enforce or display this cap.

**Recommendation:** Implement a backend counter. When 1,000 confirmed sign-ups are reached, either update the incentive copy dynamically or replace the form with a "waitlist full" message. Confirm the cap enforcement approach with the product team.

---

*ParallaxEdge Pre-Launch Page — Developer Documentation v1.0*  
*For brand and copy questions contact the brand team.*  
*For legal and compliance questions contact legal counsel before development begins.*
