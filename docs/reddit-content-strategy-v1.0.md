# ParallaxEdge — Reddit Content Strategy
**Version:** 1.0
**Date:** 2026-04-13
**Hard Launch:** June 11, 2026 (FIFA WC2026 opening match)
**Account:** u/parallaxedge (brand) + u/mfelkey_pe (founder, personal)

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-13 | Initial release |

---

## Honest Preamble

Reddit is the highest-ceiling and highest-risk social channel in this plan. Done right — genuine participation, real data, no marketing veneer — it can drive significant qualified traffic from exactly the audience ParallaxEdge needs: analytically sophisticated bettors, sports data nerds, and ML practitioners who are naturally skeptical of betting products. Done wrong — any whiff of self-promotion before trust is earned — it results in downvotes, removal, and shadow bans that are difficult to recover from.

This strategy treats Reddit as a 6-week credibility-building exercise, not a marketing channel. Product mentions are earned through community contribution, not scheduled. The X strategy can run in parallel. Reddit runs on its own timeline.

---

## 1. Subreddit Map

### Tier 1 — Primary targets (highest relevance, best fit)

**r/sportsbook**
- ~600K members
- Focus: US sports betting discussion, line shopping, bankroll management, sharp vs. square analysis. The most analytically sophisticated mainstream betting community on Reddit.
- Tone: Skeptical of tipsters and picks services. Receptive to data, methodology, and CLV discussion. Self-promotion rules are strictly enforced — accounts with no comment history get removed immediately.
- Rules relevant to PE: No self-promotion without 3+ months account history and active participation. No picks/tip content. Data posts and methodology discussions are explicitly welcomed.
- Opportunity: OC data posts (WC2022 retroactive CLV analysis), methodology discussion, CLV explainers, line movement analysis. This is the single most valuable subreddit.
- Risk: **MEDIUM** — rules are strict but the content fit is near-perfect. An account with genuine participation history will land well here.

**r/soccer**
- ~3M members
- Focus: Global football discussion — results, transfers, tactics, analytics. Large, active, diverse.
- Tone: Casual to analytical. Betting discussion is common but not the primary focus. Data posts (xG, analytics) are well-received.
- Rules relevant to PE: No spam or self-promotion. Betting content must be analytical, not promotional. Match threads are heavily trafficked.
- Opportunity: xG methodology posts, WC2026 group stage data posts, "what the underlying numbers say" commentary in match threads. Identify as a data tool, not a picks service.
- Risk: **LOW** — large community, data posts welcome, low self-promotion sensitivity if content is genuinely analytical.

**r/MachineLearning**
- ~3M members
- Focus: ML research, implementations, papers, industry discussion. Highly technical audience.
- Tone: Rigorous, skeptical of hype, appreciates methodological depth. Bayesian methods are a recurring topic.
- Rules relevant to PE: Self-promotion requires 10:1 comment-to-post ratio. Research and methodology posts are explicitly encouraged. Commercial products can be mentioned only if the post is primarily educational.
- Opportunity: "We built a Bayesian Dixon-Coles model for WC2026 — methodology writeup and Brier score validation" — this is exactly the kind of post that does well here. No mention of the product in the body; link in comments if asked.
- Risk: **LOW** — methodology is genuinely interesting to this audience. As long as it reads as a research share and not an ad, it will be received well.

**r/datascience**
- ~1.5M members
- Focus: Applied data science, career, projects, industry. Less academic than r/ML, more practical.
- Tone: Welcoming of project writeups, methodology discussions, real-world applications of ML. Sports analytics is a recurring theme.
- Rules relevant to PE: Similar 10:1 ratio requirement. Project posts allowed.
- Opportunity: "How we validate a sports betting model before deploying it — Brier score, log loss, calibration, CLV" — practical DS content that happens to be our validation framework.
- Risk: **LOW** — good content fit, receptive community.

---

### Tier 2 — Secondary targets (good fit, use after karma established)

**r/statistics**
- ~600K members
- Focus: Statistical methods, probability, inference. Technically rigorous.
- Tone: Academic. Appreciates careful methodology, critical of overclaiming.
- Opportunity: Bayesian inference for sports prediction — methodological post on why Bayesian > MLE for low-sample-size tournament data. Pure methodology, no product mention.
- Risk: **LOW** — if the post is genuinely about statistics with sports as the application domain, it fits.

**r/worldcup** (or equivalent WC2026 sub — check closer to tournament)
- Size varies; WC2026 sub likely to form or activate around May 2026
- Focus: Tournament discussion, match previews, group stage analysis.
- Opportunity: Pre-match data posts showing model probabilities vs. market — framed as analytical contribution, not picks.
- Risk: **LOW-MEDIUM** — depends heavily on the specific sub's rules. Check rules before posting.

**r/fantasyfootball** (NFL-focused)
- ~1.7M members
- Focus: NFL fantasy — not directly relevant to WC2026 but significant for NFL Phase 1C launch
- Opportunity: Post-WC2026, when NFL model launches. Not a pre-launch target.
- Risk: **LOW** — note for Phase 1C planning only.

**r/betting** (UK/EU-focused)
- ~100K members
- Focus: UK/EU sports betting, horse racing, football betting. Less analytical than r/sportsbook, more picks-adjacent.
- Opportunity: Limited. CLV methodology posts can work here but the audience is less technically sophisticated than r/sportsbook.
- Risk: **MEDIUM** — more picks-culture than r/sportsbook. Tread carefully.

---

### Tier 3 — Monitor but do not post pre-launch

**r/sportsbetting** — lower quality than r/sportsbook, more picks content, higher spam sensitivity. Monitor but do not prioritize.

**r/compsportsanalytics** — small community (~15K), niche, receptive but limited reach. Consider for Phase 2.

---

### Do Not Engage

**r/gambling** — casino-focused, not our audience, high risk of association with problem gambling content.

Any subreddit with explicit "no betting content" or "no self-promotion ever" rules. Do not attempt workarounds.

---

## 2. Account Strategy

### Two-account approach

**u/parallaxedge** (brand account)
- Created now; must be aged 2–3 months before any substantive posting in key subreddits
- Used for: official announcements, responding to direct questions about the product, launch-week posts where disclosure is required
- Do NOT use for karma-building comment participation — a brand account commenting in sports threads reads as astroturfing

**u/mfelkey_pe** (founder personal account — recommended primary vehicle)
- Used for: all genuine community participation, methodology posts, data shares, comment engagement
- This is the account that builds karma and trust. Real person, disclosed affiliation when relevant.
- Reddit strongly prefers human voices over brand accounts. The analytical community on r/sportsbook and r/MachineLearning responds to founders who can answer technical questions directly, not to brand handles.
- Disclose affiliation proactively when posting content related to ParallaxEdge: "I'm building a Bayesian betting model — here's what I've learned." This is respected. Hiding it is not.

### Karma and account age requirements

| Subreddit | Min. account age | Min. karma | Notes |
|---|---|---|---|
| r/sportsbook | ~3 months active | ~200+ | Strictly enforced; new accounts removed |
| r/soccer | ~1 month | ~50+ | More lenient but monitors |
| r/MachineLearning | ~2 months | 10:1 comment ratio | Ratio enforced by automod |
| r/datascience | ~2 months | 10:1 comment ratio | Same automod pattern |
| r/statistics | ~1 month | ~100+ | Moderate enforcement |

**Action required immediately:** Create u/mfelkey_pe now if it doesn't exist. Begin comment participation in r/sportsbook, r/soccer, r/MachineLearning this week — general contributions, not PE-related. This is karma-building, not content marketing.

### When to disclose affiliation

**Always disclose** when: posting methodology content that relates to your model, posting data from your platform, responding to questions about ParallaxEdge, posting in launch week.

**Not required to disclose** when: commenting generally in match threads (e.g., "That xG line confirms what we saw in the first half"), participating in non-PE-related discussions, answering general statistics questions.

Reddit's rules require disclosure of material connections. FTC guidelines apply. When in doubt, disclose.

---

## 3. Content Pillars (Reddit-native)

### Pillar 1 — WC2022 Retroactive CLV Analysis
**"We ran our Bayesian Dixon-Coles model on WC2022 retroactively — CLV results across 46 Pinnacle matches"**

This is the single highest-value Reddit post in the pre-launch plan. It proves the model works without asking anyone to trust a claim.

- Target: r/sportsbook (primary), r/soccer (secondary)
- Format: Long-form text post with data table showing match, predicted edge, actual CLV, result
- Tone: Methodological, honest about losses, transparent about the framework
- Identify PE: Yes — "I'm building a tool called ParallaxEdge that uses this model. Not here to pitch it — sharing the validation methodology."
- When: Week 3 (after karma established). This is the most important single post pre-launch.
- What makes it work: The r/sportsbook community has seen hundreds of tipsters claim good records. Showing actual CLV data with losses included — rather than cherry-picked wins — signals legitimacy instantly.

### Pillar 2 — Bayesian Model Methodology Deep Dive
**"Why we use Bayesian inference instead of MLE for a tournament with 32 teams and limited match data"**

- Target: r/MachineLearning, r/datascience, r/statistics
- Format: Long-form text post. Explain the problem (low sample size per team in tournament settings), why MLE produces overconfident estimates, how Bayesian posterior gives you calibrated uncertainty, Brier score comparison.
- Tone: Technical but accessible. Written as a learning share, not a product pitch.
- Identify PE: Mention in passing ("I'm applying this to a WC2026 betting model") — do not lead with it
- When: Week 2 (r/ML/DS are more forgiving on account age than r/sportsbook)
- What makes it work: Bayesian methods in sports analytics is a legitimate ML topic. The WC2026 application makes it timely. The Brier score comparison gives it empirical teeth.

### Pillar 3 — xG as a Predictor vs. Goals: Empirical Analysis
**"xG outperforms goals as a predictor of future results — here's the data from UCL and WC matches"**

- Target: r/soccer, r/datascience
- Format: OC data post with visualisation or table. Show prediction accuracy (Brier score) for goals-based vs. xG-based model over the StatsBomb dataset.
- Tone: Data journalism style. Show the finding, explain the methodology, invite critique.
- Identify PE: Optional — can be posted purely as a data analysis without PE mention on first posting
- When: Week 2–3
- What makes it work: The xG debate is perpetually active on r/soccer. A post that actually measures the predictive difference (not just argues for it) will get engagement.

### Pillar 4 — WC2026 Group Stage Market Efficiency Analysis
**"Where WC betting markets have historically mispriced outcomes — and what the data says about WC2026"**

- Target: r/sportsbook, r/worldcup
- Format: Data post. Show historical WC market efficiency patterns — which team types / match types tend to be mispriced, backed by Pinnacle closing line data.
- Tone: Analytical, hedged. "Here's what the historical data suggests — not a prediction."
- Identify PE: Yes — frame as preview of what the model will track in real time during WC2026
- When: Week 5–6 (May, closer to WC2026)
- What makes it work: r/sportsbook loves this kind of structural market analysis. It's the exact opposite of "here are my picks."

### Pillar 5 — Live Match Thread Participation (WC2026 opening match, June 11)
Not a standalone post — participation in existing match threads with real-time model data.

- Target: r/soccer match thread, r/worldcup match thread, r/sportsbook live discussion
- Format: Comments with real data: "Our model had Mexico at 34% win probability pregame. Half-time xG is 0.4 vs 0.9 — aligns with the current market movement."
- Identify PE: Yes, briefly — "I run a betting analytics platform — tracking CLV on this match in real time."
- When: June 11 opening match
- What makes it work: Match threads move fast. Real-time data commentary during a major match gets visibility. No links required — the brand name is the CTA.

---

## 4. Pre-Launch Participation Plan (April 13 – June 10)

### Weeks 1–2: April 13–26 — Karma building only, no PE-adjacent content

**u/mfelkey_pe actions:**
- Comment in r/sportsbook on CLV discussions, line movement posts, market efficiency threads. Contribute genuine analysis. Do not mention PE.
- Comment in r/soccer on xG-related posts, tactical analysis, analytics discussions.
- Comment in r/MachineLearning on Bayesian inference threads, sports prediction threads.
- Target: 20–30 quality comments across the three subreddits. Quality over quantity — one thoughtful comment beats five one-liners.

**u/parallaxedge actions:**
- Account created, no posts, no comments. Let it age.

**Do not post:** No original posts yet. No PE mentions. Just participate as a knowledgeable community member.

---

### Week 3: April 27 – May 3 — First original post

**Post: WC2022 Retroactive CLV Analysis** (Pillar 1)
- Post to r/sportsbook
- This is the most important post in the pre-launch plan. Spend time on it. Include actual data table from `odds_clv_cache`. Show losses. Show the full 46-match record.
- Title: "I backtested a Bayesian Dixon-Coles model on WC2022 Pinnacle lines — here are the CLV results across all 46 matches (with losses)"
- Disclose affiliation in the body: "I'm building a WC2026 betting analytics platform. This is our validation dataset. Happy to answer questions on methodology."

**Continue:** Comment participation in all three primary subreddits.

---

### Week 4: May 4–10 — Methodology post in ML/DS communities

**Post: Bayesian vs MLE methodology post** (Pillar 2)
- Post to r/MachineLearning or r/datascience (check which has better engagement that week)
- Title: "Bayesian Dixon-Coles for tournament football — why posterior uncertainty matters more than point estimates in low-sample-size settings"
- Include the Brier score comparison. Technical depth earns credibility here.
- Minimal PE mention — "building a WC2026 application of this" is sufficient.

**Continue:** Comment participation. Begin monitoring r/worldcup for activity level — a WC2026-specific sub may be growing by now.

---

### Week 5: May 11–17 — xG analysis post

**Post: xG vs goals empirical analysis** (Pillar 3)
- Post to r/soccer
- Title: "Empirical comparison: xG vs actual goals as predictors of future match outcomes — data from 128 WC and UCL matches"
- Use StatsBomb data. Show the Brier score improvement. Visualisation if possible.

**AMA question:** Is an AMA appropriate pre-launch?
- **Not yet.** AMAs work best when the product is live and there's something concrete to discuss. A pre-launch AMA risks "cool idea, come back when it's real" reception. Recommend scheduling an AMA on r/sportsbook or r/soccer for Week 2 post-launch (late June), when WC2026 CLV results are accumulating.

---

### Week 6: May 18–24 — WC2026 market efficiency post

**Post: WC2026 market efficiency analysis** (Pillar 4)
- Post to r/sportsbook
- Title: "WC betting market efficiency — where the closing line has historically been most wrong, and what our model is watching for WC2026"
- This is the first post that explicitly connects the content to an upcoming launch. Keep the product mention proportionate — the data is the content.

---

### Weeks 7–8: May 25 – June 10 — Pre-launch build

- Continue comment participation. Engage with any responses to previous posts.
- Post WC2026 group stage data post to r/worldcup or r/soccer if appropriate sub exists.
- Do not post in r/sportsbook again until launch week — space posts to avoid spam perception.
- Begin monitoring r/sportsbook for WC2026 preview threads — participate as a data contributor, not a promoter.

---

## 5. Launch Week Plan (June 1–11)

### June 1–10: Pre-launch build

- Respond to any outstanding comments on previous posts.
- Comment in WC2026 preview threads on r/soccer and r/sportsbook with model data. Brief, data-forward, no hard sell.
- Do not post standalone promotional content. The groundwork has been laid — let it work.

### June 11: Launch day

**Post 1 — r/sportsbook:**
Title: "We built a Bayesian betting intelligence platform for WC2026 — it's live today. Here's the opening match signal and our methodology."

Body structure:
1. Brief intro: what ParallaxEdge is, what it does, what it doesn't do (not a tipster)
2. Opening match signal: Mexico vs South Africa probabilities, edge, confidence — real data
3. Link to /methodology page and /track-record
4. Free tier available, first 1,000 get Sharp free — mentioned once, not the headline
5. "Happy to answer questions on the model architecture"

**Post 2 — r/MachineLearning or r/datascience:**
Title: "Our Bayesian sports betting model is live for WC2026 — methodology writeup and public track record"

Body: Focus on the technical implementation — PyMC, NUTS, Dixon-Coles extension, Brier score validation. Product mention secondary.

**Match thread participation — June 11:**
- Comment in r/soccer Mexico vs South Africa match thread with pre-match model data
- Comment in r/worldcup match thread same
- Post CLV result update in r/sportsbook after the match

### Responding to skeptical/hostile comments

This will happen. Playbook:

**"This is just another tipster"**
→ "Understood skepticism — that's exactly why we track CLV publicly, not win rate. Here's our WC2022 backtest with losses included: [link]. Judge the methodology, not the claim."

**"Betting models don't work / the market is efficient"**
→ "Markets are highly efficient at closing, which is exactly why CLV is our primary metric. We're not claiming to beat the market systematically — we're publishing signals and letting the CLV record speak. Here's what the WC2022 backtest showed: [specific data point]."

**"How is this different from [competitor]?"**
→ "Happy to discuss methodology differences. The main distinction is the Bayesian framework — we give you a confidence interval, not just a probability. Full methodology at [link]."

**"You're going to lose money / this is gambling"**
→ "Agreed that most people lose. The platform is a decision-support tool — we show what the model sees, users make their own decisions. 18+ only, responsible gambling resources are on the site."

**Aggressive/hostile with no engagement value:**
→ Do not respond. Upvote thoughtful skepticism. Downvote nothing.

---

## 6. Rules Compliance Checklist

| Subreddit | Key rules to follow | Risk of removal |
|---|---|---|
| r/sportsbook | No picks. No affiliate links. Must have comment history. Disclose affiliation on PE-related posts. | HIGH if posting without karma. MEDIUM with established account. |
| r/soccer | No spam. No affiliate links. Betting content must be analytical. | LOW with analytical content. |
| r/MachineLearning | 10:1 comment-to-submission ratio. No commercial pitches. Educational content allowed. | MEDIUM — automod enforces ratio strictly. |
| r/datascience | Same 10:1 rule. Project posts allowed with context. | MEDIUM — same automod. |
| r/statistics | No low-effort posts. Statistical claims require sourcing. | LOW with rigorous content. |
| r/worldcup | Check rules at time of posting — sub rules vary by tournament cycle. | UNKNOWN — verify before posting. |

**Subreddits where PE content is HIGH risk regardless of approach:**
- r/gambling — do not post
- Any subreddit with explicit "no self-promotion ever" rules — do not attempt workarounds
- New subreddits created during WC2026 hype — check rules carefully before assuming they're open

---

## 7. Reddit-Specific Voice Guide

### How the ParallaxEdge voice adapts for Reddit

Reddit is peer-to-peer. The polished brand voice of the website and X does not transfer. On Reddit, you are a person talking to people, not a brand broadcasting to an audience.

**Right:** "I've been working on a Bayesian model for WC2026 betting markets. Here's something I found in the WC2022 data that surprised me..."

**Wrong:** "ParallaxEdge is an AI-powered betting intelligence platform that surfaces opportunities most of the market misses. Try it free at..."

The difference is not just tone — it's the fundamental relationship between the poster and the reader. Reddit values the first framing and punishes the second.

### Phrases and framings to avoid

- Any marketing copy phrasing: "AI-powered," "game-changing," "cutting-edge"
- Certainty claims: "our model predicts," "guaranteed edge," "will beat the market"
- Urgency tactics: "limited time," "first 1,000 only" — save for the product page, not Reddit posts
- Unprompted links: Only link to the site when directly relevant or asked
- Hollow disclaimers tacked on as afterthoughts: "18+ only, bet responsibly" as a sign-off feels performative on Reddit; address responsible gambling substantively if the topic comes up

### The show-don't-tell principle

Every Reddit post should lead with data or methodology, not claims about the platform. The sequence is always:

1. Here's something interesting in the data
2. Here's the methodology behind it
3. Here's what it means for WC2026
4. (Optional, proportionate) I'm applying this in a platform I'm building

Never lead with the product. The product is the conclusion, not the premise.

### How to handle criticism

Skepticism on Reddit is a feature, not a bug. The r/sportsbook community has been burned by tipsters, sports analytics startups that overpromise, and model-sellers who cherry-pick results. Their skepticism is earned and correct.

Respond to skepticism with data, not defensiveness. If someone challenges the model, show the validation data. If someone challenges the methodology, explain it in detail. If someone says "this won't work," engage with the specific objection rather than dismissing it.

The surest way to earn credibility on Reddit is to take criticism seriously and respond rigorously. The surest way to lose it is to get defensive or dismiss objections.

---

## 8. Success Metrics

These are honest targets for a sole-founder operation with a 6-week pre-launch window. Reddit success is slow and uneven — a single well-received post can drive more traffic than weeks of engagement.

| Metric | Target by June 11 |
|---|---|
| u/mfelkey_pe karma | 500+ (comment karma from genuine participation) |
| u/parallaxedge karma | 100+ (minimal — brand account is secondary) |
| Upvotes on WC2022 CLV post (r/sportsbook) | 50+ (a strong post in this sub) |
| Comments on methodology post (r/ML or r/DS) | 20+ |
| Reddit referral traffic to parallaxedge.com | 200+ sessions pre-launch |
| Launch day post upvotes (r/sportsbook) | 100+ |
| Post-launch CLV thread upvotes | 50+ per match |

**Realistic expectations:**

Reddit will not be a primary traffic driver pre-launch. It is a credibility layer. The r/sportsbook community talking positively about ParallaxEdge — or even engaging with it critically — is worth more than 10,000 TikTok views because the audience is exactly right. One converted r/sportsbook user is more valuable than 50 casual Instagram followers.

Measure success by quality of engagement, not volume. A 20-comment thread on r/sportsbook where experienced bettors are discussing the CLV methodology is a better outcome than 500 upvotes on a low-engagement viral post.

---

*Document produced: 2026-04-13*
*Ref: x-content-strategy.md v1.0 | Brand Guide v1.3 | Marketing Plan v2.1 | Responsible Gambling Policy v1.2*
*Subreddit rules change. Verify current rules before posting in any subreddit.*
