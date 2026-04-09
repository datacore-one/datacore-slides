---
name: Slides for Datacore
description: "Presentation generation — Gamma.app integration, slide indexing, and content compilation"
version: 1.0.0
author: datacore-one
license: MIT
tags: [slides, presentations, gamma, powerpoint]
x-datacore:
  module: slides
  tools: 0
  skills: 3
  agents: 3
  commands: 0
  workflows: 0
  engram_count: 0
  injection_policy: on_match
  match_terms: [slides, presentation, gamma, powerpoint, deck, pitch]
---

# Slides for Datacore

Presentation generation via Gamma.app — create presentations from content,
index existing decks, and sync with Gamma workspace.

## What This Module Provides

**Skills** (3): create-presentation, index-presentation, sync-gamma

**Agents** (3):
- `gamma-presentation-generator` — Generate presentations via Gamma
- `gamma-slide-indexer` — Index existing presentations
- `presentation-generator` — General presentation routing

## When to Use

Triggers: slides, presentation, gamma, powerpoint, deck, pitch.
