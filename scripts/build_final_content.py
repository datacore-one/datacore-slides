#!/usr/bin/env python3
"""
Build _final_content.json for the Dubai entity two-pagers from the workflow's
auditor-loop output — compressed to the fixed renderer layout budget and
de-hedged, with the required disclaimer. Single source of truth for PDF + md.

Run: python3 build_final_content.py
Writes: 1-datafund/1-tracks/comms/proposals/dubai-twopagers/entities/_final_content.json
"""
import json
from pathlib import Path

OUT = Path("/Users/gregor/Data/1-datafund/1-tracks/comms/proposals/dubai-twopagers/entities/_final_content.json")

FINAL = {
  "dubai-government": {
    "name": "Dubai Government",
    "p1_title": ["Institutional Memory", "for Sovereign AI."],
    "p1_subtitle": "A sovereign memory layer Dubai's government owns — judgement that compounds.",
    "opportunity_title": "Memory is the box your own architecture already drew.",
    "opportunity_paras": [
      "A senior official settles a hard cross-entity licensing exception one Sunday: the ruling, the reasoning, the correction. PLUR captures it in-workflow as a typed, classified record in that entity's own store. By Monday, an agent in that entity meets a like case and recalls it. The decision compounds, on the government's network.",
      "Dubai's own AI Integration Matrix names an internal-RAG, institutional-knowledge quadrant. But retrieval fetches documents; it does not retain the rulings and corrections documents leave out. PLUR fills that box — built and running internally for our own team today, in preparation for sovereign deployment, not a slideware concept.",
      "Cross-entity reuse is never automatic. Promoting a precedent beyond its owning entity is an explicit, logged, revocable governance action with a named owner. Run on Dubai's own infrastructure, beneath the algorithm bank, PLUR turns isolated pilots into one capability the government owns and no vendor can switch off.",
    ],
    "plur_concrete": "An engram is a typed record — ruling, reasoning, correction — carrying provenance, a decay weight so stale rulings fade, and a feedback score that strengthens what proves right. Worked case: two entities log opposite rulings on a similar waiver; recall returns both, flagged as conflicting, for a human to reconcile rather than silently picking one.",
    "p2_title": ["Seed one entity.", "Govern the precedent layer.", "Make Dubai the showcase."],
    "phases_title": "From one entity to a sovereign capability the whole government compounds.",
    "phases": [
      ["0", "Foundation", "Accreditation gate", "Deploy on government infrastructure, keys held by the government. Security accreditation (NESA, ISO 27001) gates the build clock."],
      ["1", "One entity", "8-12 weeks", "Seed one entity from its logged exceptions; agents recall real precedent. Read-only beside live systems. First outcome <= 60 days."],
      ["2", "Across government", "Months 3-9", "Engrams stay entity-scoped; cross-entity promotion is explicit, logged, revocable, curated. Recall honours classification and surfaces conflicts."],
      ["3", "Federal showcase", "Months 9-12+", "A sovereign capability the government owns under Dubai Data Law — exportable, that no vendor can switch off."],
    ],
    "use_cases": [
      "Upgrade institutional-knowledge access from document lookup to retained judgement: agents decide a recurring exception the way the institution already decided it, with fewer escalations. Humans still own the sign-off that matters.",
      "What RAG cannot do: engrams carry a type, a decay weight, and a feedback score. When two precedents disagree, recall flags both for a human rather than blending them — the single clearest line against internal-RAG.",
      "Sovereign by enforcement, not assertion: engrams live on government infrastructure, keys government-held, source of truth in plain-text YAML. The no-outbound-call property is enforced by egress policy and verifiable by independent audit of the Apache-2.0 source.",
      "Why not build it yourself: a YAML store takes a quarter; the operational discipline — feedback-trained recall, decay and conflict semantics, curation — takes years. Co-development: the government co-owns the capability under Apache 2.0. The captured judgement stays yours to fork.",
      "Government-grade track record: Fairdrop and Fairdrive deployed, a core contribution to Ethereum Swarm, PLUR Enterprise running internally. Eight years on data sovereignty (Datafund 2017); 3x MyData Operator Award (2021-23); co-author of CEN/CENELEC CWA 17525:2020.",
      "Horizon: the same substrate the federal AI and Data Authority can study, and the agentic-government model the nation can export as soft power — built and owned inside the UAE's borders.",
    ],
    "disclaimer": "Prepared from publicly available information on Digital Dubai's AI programme; named initiatives, figures and security posture to be confirmed with stakeholders.",
    "context_note": "Umbrella / master narrative for the entity set. GD: H.E. Hamad Obaid Al Mansoori, Director-General, Digital Dubai.",
  },

  "rta": {
    "name": "Roads and Transport Authority (RTA)",
    "p1_title": ["Institutional Memory", "for Sovereign AI."],
    "p1_subtitle": "A sovereign, recall-only memory layer RTA's AI agents own.",
    "opportunity_title": "RTA already runs the agents. PLUR gives them a memory RTA owns.",
    "opportunity_paras": [
      "Across the AI initiatives RTA has publicly described, every agent re-derives context each session. A ruling one agent makes is lost to the next. RTA's Big Data Platform holds data, not this reasoning. The institution scales tools, not a learning institution.",
      "An engram is one captured ruling: the decision, the conditions it holds under, and when. PLUR captures, stores and serves that reasoning on RTA hardware, so agents accumulate judgement. RTA owns the substrate outright — Apache 2.0, plain-text YAML, exportable — not the vendor.",
      "A safety bright-line first: this is recall-only, for decision review. No engram ever touches live signal timing or autonomous-mobility control. The differentiator over a RAG or Mem0 cache is checkable: a scope engine rejects a ruling whose conditions don't match before it reaches the agent.",
    ],
    "plur_concrete": "A worked example: an engineer overrides an agent on a flooded junction and records why. PLUR stores it as a scoped, timestamped engram on RTA hardware. The scope engine matches its recorded conditions — flood — and offers it only then; a dry-junction or conflicting precedent is rejected before the agent sees it. Recall-only, for review.",
    "p2_title": ["Start with one team.", "Scale one pillar at a time.", "Make RTA's autonomy governable."],
    "phases_title": "From one Cognitive Licensing team to an exportable governance pattern other UAE entities adopt.",
    "phases": [
      ["1", "Sandbox", "~60 days", "PLUR offline on a segmented VM for one Cognitive Licensing team. First outcome <= 60 days after internal approvals clear."],
      ["2", "Scale", "Per pillar", "Extend via a non-invasive memory API; vendor agents read and write engrams, no re-engineering. Curated and reversible."],
      ["3", "Govern", "Quarters 3-4", "Recall wired to RTA's audit and explainability commitments: append-only signed chain, RTA-held keys, four-eyes on destructive actions."],
      ["4", "Horizon", "On RTA's terms", "RTA becomes the proving ground for governable agentic government — a sovereign, exportable reference pattern."],
    ],
    "use_cases": [
      "Cognitive Licensing agents share one governed engram pack of policy and edge-case precedent, so a ruling made once is applied consistently authority-wide — the strongest first, non-production deployment, measured against RTA's own baseline.",
      "Traffic and digital-twin signal agents gain a recall-only after-action layer: human override rulings are captured for review, scope-checked, and never touch live signal timing — a safety bright line regulators can verify.",
      "Mahboub recalls prior resolutions and Arabic/English phrasing precedents instead of re-deriving them each session — tested as a falsifiable answer-consistency hypothesis on a fixed query set, not an asserted improvement.",
      "An expert's override is captured the instant it happens, turning tacit operator judgement into a durable, RTA-owned asset as RTA digitises its workforce skills.",
      "Every recall and override is timestamped, scope-checked and access-controlled on RTA's own hardware — supporting data-residency and the explainability trail RTA has publicly committed to.",
      "RTA owns the store outright: self-host with no dependency on Datafund, fork the Apache-2.0 code, and export 100% of memory in plain-text YAML if the relationship ever ends. Horizon: this governed memory may one day stand as a sovereign asset RTA owns and never trades.",
    ],
    "disclaimer": "Stated plainly: PLUR is dogfood-tested inside the Datafund team, not yet sovereign-deployed at an institution; no live pilot is claimed. Details to be confirmed with RTA.",
    "context_note": "GD: Mattar Al Tayer, Director-General & Chairman of the Board of Executive Directors, RTA. Grounded in RTA AI Strategy 2030.",
  },

  "dewa": {
    "name": "Dubai Electricity and Water Authority (DEWA)",
    "p1_title": ["Institutional Memory", "for Sovereign AI."],
    "p1_subtitle": "DEWA owns the judgement; the foreign model becomes swappable.",
    "opportunity_title": "Today the judgement is captive to the vendor. PLUR makes it DEWA's.",
    "opportunity_paras": [
      "Each AI agent DEWA runs reasons from a foreign vendor's model, and that reasoning resets every session. The strategic exposure is dependency: a decade of accumulated national engineering judgement stays locked to whichever model executes it. Swap the model, lose the judgement.",
      "PLUR inverts that. It is a private, on-premise memory layer that captures DEWA's own corrections and the reasoning behind them, then serves them back to any agent. The judgement becomes a sovereign asset DEWA owns outright — the model becomes a commodity DEWA can change at will.",
      "The operational payoff sits underneath: when a senior engineer retires, their reasoning no longer leaves with them. We can show one concrete proof — a correction captured at the AI Virtual Engineer, retrieved on demand, and surviving a swap of the model beneath it.",
    ],
    "plur_concrete": "A senior engineer corrects an agent on a fault and records why. PLUR stores that correction-plus-rationale on-prem as a structured record. Swap the underlying model and the correction still retrieves. When a second engineer disagrees, the conflict surfaces for a named DEWA reviewer rather than silently overwriting — the human owns the resolution.",
    "p2_title": ["Prove portability, air-gapped.", "Validate one agent.", "Then a national pattern."],
    "phases_title": "From one team's portable judgement to a sovereign memory pattern the UAE can replicate.",
    "phases": [
      ["1", "Prove", "~60 days", "Read-only, air-gapped, no path to OT/SCADA. A named validator confirms corrections retrieve and survive a model swap."],
      ["2", "Validate", "3-6 months", "Validate one agent end-to-end in a sandbox; design fleet integration together. Full standalone value either way."],
      ["3", "Govern", "6-12 months", "Pre-inference classify, filter and redact under DEWA's key, full audit log; sensitive tiers restricted to sovereign-hosted models."],
      ["4", "Replicate", "Horizon", "DEWA becomes the sovereign-memory reference pattern the UAE can replicate across its entities."],
    ],
    "use_cases": [
      "Make the judgement portable: a correction captured at one of DEWA's agents is stored on-prem and provably retrieved after the underlying foreign model is swapped. DEWA owns the reasoning, not the vendor — with expert-retirement knowledge retention as the payoff underneath.",
      "Keep PLUR itself sovereign: fully self-hosted with zero outbound connections — no telemetry, no license phone-home, no model calls. Plain-text exportable YAML under Apache 2.0, with a written exit plan. We back the zero-outbound claim with a network-capture test DEWA runs in its own tenancy.",
      "Resolve contradicting corrections rather than overwrite them: when two senior engineers disagree, the conflict surfaces to a named DEWA reviewer before any agent reads it — governance a vector store does not give you by default.",
      "Run one DEWA-owned store behind connected agents through a read-only governed endpoint, so a correction captured at one agent is read by every agent, consistent regardless of which model executes.",
      "Govern the inference-time path explicitly: define exactly what crosses the border, in what redacted form, under whose key, with what audit log — and restrict sensitive tiers to sovereign-hosted models. On-soil residency plus pre-inference filtering, not residency alone.",
      "Pair each agent decision with the human corrections and rationale around it — an auditable, DEWA-owned record of reasoning. Memory makes the decisions accountable; it does not make the agents autonomous, and we do not claim it does.",
    ],
    "disclaimer": "Prepared from publicly available information on DEWA's published initiatives and leadership priorities; any attributed figure to be confirmed against DEWA's own sources.",
    "context_note": "GD: H.E. Saeed Mohammed Al Tayer, MD & CEO, DEWA. Grounded in the AI-native-utility roadmap, Rammas and the AI Virtual Engineer.",
  },

  "dld": {
    "name": "Dubai Land Department (DLD)",
    "p1_title": ["Institutional Memory", "for Sovereign AI."],
    "p1_subtitle": "DLD's valuation judgement — compounding, owned inside the Emirate.",
    "opportunity_title": "DLD's hardest-won judgement isn't accumulating anywhere DLD owns.",
    "opportunity_paras": [
      "DLD made Dubai the MENA-first regulated real-estate tokenisation registry — Prypco Mint, a live secondary market, AED 60B (USD 16B) targeted by 2033. That trophy rests on one thing: trustworthy valuation. Yet the judgement layer interpreting deeds sits in foreign clouds.",
      "In registries like yours we typically see two costs. AI tools quote listing prices the registry has already superseded. And staff re-disambiguate post-handover building names by hand, the knowledge trapped in analysts' heads. A memory layer stops the AI repeating a known-wrong answer twice.",
      "The sovereignty stake is sharper still. Dubai's Data Law makes deeds government-owned assets — but the nation that owns its accumulated machine reasoning owns its agentic future. A memory layer inside the Emirate keeps that reasoning under Dubai's control, advancing the D33 and Real Estate Strategy 2033 agenda.",
    ],
    "plur_concrete": "Illustration: a Business Bay tower is renamed post-handover; its building code is ambiguous. DLD maps alias to canonical building once, confirmed by a reviewer. Every agent now resolves that tower correctly instead of re-disambiguating by hand — deterministic, auditable, accumulating. A valuer's override on a comparable follows the same path, with a review-trigger so stale comps expire.",
    "p2_title": ["The memory layer under your agents.", "Start with one desk.", "Prove it, then reuse it nationally."],
    "phases_title": "From one valuation desk to a federal sovereign-memory layer any UAE entity can query.",
    "phases": [
      ["1", "One desk", "~60 days", "A side panel valuers consult — never auto-applied, nothing leaves the Emirate. First outcome <= 60 days after provisioning."],
      ["2", "Grounding", "~90 days", "Agents query for confirmed corrections and get an answer, not the raw store — air-gapped; classify-and-redact fails closed."],
      ["3", "Governed recall", "~90 days", "Every answer traces to the correction behind it. Supersession and temporal-validity expiry keep stale comps out."],
      ["4", "National standard", "Horizon", "The same air-gappable layer becomes a federal standard another UAE registry or ministry can query."],
    ],
    "use_cases": [
      "Building-name aliases and post-handover renames become queryable memory — the primary proof. Alias-to-canonical mapping is deterministic, low-risk, auditable: every agent maps a transaction to the right building instead of re-disambiguating it by hand.",
      "A valuer's confirmed override becomes an engram with an expiry or review-trigger, so agents stop repeating a pricing error the registry has already corrected — without surfacing a stale, market-specific comp later.",
      "One confirmed correction is recalled everywhere: a policy nuance or dispute precedent taught once reaches every agent, read-side first, with write-back only where a vendor API allows and DLD approves.",
      "Workforce rotation stops draining knowledge — a departing expert's reviewed judgement stays in the store and is inherited by the agents that remain.",
      "Every agent answer is auditable back to the specific confirmed engram behind it, with supersession, temporal-validity and a human-confirms gate — accountability a regulated registry can defend to RERA and leadership.",
      "The wedge over a sovereign-region vendor knowledge base is structural: cross-vendor neutrality, survives-vendor-exit, and first-class provenance not locked inside one hyperscaler's stack. The judgement layer stays Dubai's, not a single cloud's.",
    ],
    "disclaimer": "Prepared from publicly available information on DLD's stated initiatives — Prypco Mint, D33, Real Estate Strategy 2033 — to be refined with stakeholders.",
    "context_note": "GD: Omar Bushahab, Director-General, DLD (appointed May 2025). Grounded in the Prypco Mint tokenisation programme.",
  },

  "dib": {
    "name": "Dubai Islamic Bank (DIB)",
    "p1_title": ["Institutional Memory", "for Sovereign AI."],
    "p1_subtitle": "DIB's Shariah-aligned rulings, owned by the bank, recalled by every agent.",
    "opportunity_title": "Define the reference standard for Shariah-governed AI memory — an asset DIB owns.",
    "opportunity_paras": [
      "DIB is deploying responsible AI with HCLTech and modernising its core with IBM. The strategy is sound. The first-mover prize sits one layer above it: become the bank — and the nation — that defines how Shariah-governed AI remembers its own rulings, under Dubai's AI agenda.",
      "An engram is a short, human-readable record of a decision — we ruled X because Y — stored as plain YAML with named-scholar attestation and scope. When a scholar or credit reviewer corrects an AI call, that ruling becomes recallable and citable into the next agent's context.",
      "Your watsonx.governance and HCLTech stacks already log human overrides. The board's open question: is that log a portable, model-agnostic asset DIB keeps across model generations and vendors — or a vendor-coupled entry? PLUR makes it the former.",
    ],
    "plur_concrete": "Thursday, a DIB credit reviewer overturns an AI rejection: the profit-sharing structure is sound under the Shariah board's ruling — re-run without the collateral flag. The scholar of record signs it; it is scope-tagged (madhhab, product, jurisdiction) and stored locally as an engram. Friday, an underwriting agent recalls and cites it. Raw customer data never moved.",
    "p2_title": ["Observe one Shariah team.", "Scale the memory across DIB.", "A national reference pattern."],
    "phases_title": "From one observed team to a UAE reference pattern a national sponsor can custody.",
    "phases": [
      ["1", "Sandbox", "~60 days", "One named team; PLUR ingests DIB-owned decision logs in observation mode. Co-signed success metric and baseline first."],
      ["2", "Scale", "Quarters 2-3", "Extend the engram layer above the HCLTech and IBM stacks across credit, fraud and advisory. Supersession is scholar-attested."],
      ["3", "Federate", "Year 1-2", "Only the ruling abstraction crosses borders; regulated data stays resident. A UAE sponsor can custody the pattern."],
      ["4", "Horizon", "Year 2+", "A UAE-owned, exportable approach to Shariah-governed AI memory — soft power through DIB's Islamic-finance footprint."],
    ],
    "use_cases": [
      "Shariah-board auditability: every reviewed AI decision carries a human-readable engram — the ruling, the scholar of record, the scope. The board audits the human ruling around the model. The delta over watsonx.governance: this record is portable, model-agnostic, and recall-injected into the next agent.",
      "A concrete engram the board can read: a YAML record with ruling, rationale, scholar_of_record, madhhab, product, jurisdiction, supersedes, status, version — cited verbatim at recall. A governance log records that an override happened; the engram carries why, who ruled, and the scope it binds.",
      "Multi-madhhab disambiguation: when two in-scope rulings legitimately disagree across madhhab or jurisdiction, recall returns both, scope-qualified, and routes the conflict to the scholar of record — supersession is attested, never newest-wins. A human decision by design.",
      "Recall quality made falsifiable: precision is a measured hypothesis, not a claim. We define the metric, the labelled case set, and the failure mode so your model-validation and risk teams can stress-test it before Phase 1. On a near-miss, recall abstains and escalates.",
      "Cross-jurisdiction recall: only the ruling abstraction crosses boundaries between DIB's international markets; raw regulated data stays resident under each regulator. The same scoped ruling memory generalises to agentic government.",
      "Exit without lock-in: on exit, DIB keeps every engram as open YAML — the full corpus of rulings, attestations and scope, re-importable into any engine. What DIB loses is PLUR's curation and recall engine, not the asset itself.",
    ],
    "disclaimer": "Prepared from publicly available information on DIB's initiatives and leadership statements (including GITEX 2025); footprint and regulator references to be confirmed with the bank.",
    "context_note": "Recycled Lloyds spine, re-skinned for Islamic finance. GD: Dr. Adnan Chilwan, Group CEO, DIB.",
  },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(FINAL, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {OUT} ({len(FINAL)} entities)")
for k, v in FINAL.items():
    op = [len(p.split()) for p in v["opportunity_paras"]]
    pc = len(v["plur_concrete"].split())
    ph = [len(p[3].split()) for p in v["phases"]]
    print(f"  {k}: opp={op} concrete={pc} phase_body={ph} subtitle_wc={len(v['p1_subtitle'].split())} opptitle_wc={len(v['opportunity_title'].split())}")
