# NEXUS — RL Training

This directory contains the research/training side of NEXUS, separate from
the deployed web app. The deployed backend uses Groq's hosted LLM for code
generation (fast, free, reliable, zero GPU needed). This notebook is for the
part of the project that's genuinely research work: fine-tuning a small
open-weight model with **Reinforcement Learning from Verifiable Rewards
(RLVR)**, using the exact same verification logic that powers the backend.

## What this proves

Most student "AI coding" projects stop at prompting an API. This shows you
can take a model, define a real verifiable reward signal (not a vibes-based
LLM judge), and run policy optimization (GRPO) to measurably improve it —
the same family of technique behind DeepSeek-R1 and most 2025-2026 reasoning
model post-training.

## How to run it

1. Open `nexus_rl_training.ipynb` in Google Colab
   (`File -> Upload notebook`, or push this repo to GitHub and open directly
   from there via `File -> Open notebook -> GitHub`).
2. `Runtime -> Change runtime type -> T4 GPU` (free tier).
3. `Runtime -> Run all`. Takes roughly 20-40 minutes.
4. The notebook prints **real, live-measured** baseline vs. post-RL pass@1
   numbers at the end. Copy those exact numbers — don't substitute different
   ones — into your README/resume ablation table.

## If you'd rather train on your own GPU / laptop CPU

- **Laptop CPU only**: skip this notebook. A 0.5B model GRPO run is
  painfully slow without a GPU. Instead, run `evaluate_baseline.py` to get
  a baseline pass@1 number for whichever LLM you're using (e.g. via Groq's
  API) with zero training — this still gives you a legitimate number to
  report ("baseline pass@1 without RL: X%").
- **Local GPU (even a modest one, e.g. 8GB VRAM laptop GPU)**: the notebook
  should run close to as-is locally; just `pip install` the same versions
  pinned in the first cell inside a fresh virtualenv, and point
  `device_map='auto'` will pick up your GPU automatically.

## Honesty checklist before you put numbers on your resume

- [ ] Did you actually run the notebook top to bottom yourself?
- [ ] Are the numbers in your README the exact ones printed by the notebook
      (not rounded up, not "approximately", not copied from this template)?
- [ ] If GRPO didn't improve the score on your run (it might not, small
      models + 1 epoch + ~300 prompts is a genuinely modest training run),
      report that honestly too — "I implemented RLVR fine-tuning end to end;
      on a 1-epoch/300-prompt run the improvement was within noise, which is
      itself a fair characterization of what it takes to move a 0.5B model
      with GRPO" is a STRONGER interview answer than a suspiciously perfect
      number, because it shows you understand what you built.
