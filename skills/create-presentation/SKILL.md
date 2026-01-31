---
name: create-presentation
description: Smart presentation creation wizard using Gamma.app or Gemini image composition
user-invocable: true
---

# Create Presentation

## Instructions

Follow the full workflow in `~/Data/.datacore/modules/slides/commands/create-presentation.md`.

Usage: `/create-presentation [topic or description]`

Parse `$ARGUMENTS` for topic. Routes to Gamma.app API or Gemini image composition based on user choice. Supports brand templates and slide reuse from index.
