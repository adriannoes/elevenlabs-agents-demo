# Notes that would make good upstream patches

Mechanical mismatches between [`elevenlabs/skills`](https://github.com/elevenlabs/skills) and canonical [Models](https://elevenlabs.io/docs/overview/models), observed from this lab. Re-check before sending a PR — the live diff is:

```bash
uv run python scripts/skills_model_drift.py
```

This page is a **patch sketch**, not a claim that a PR is already open.

## 1. Mark Turbo deprecated in `text-to-speech/SKILL.md`

**File:** `text-to-speech/SKILL.md` (Models table).

**Change:** keep the Turbo rows if the IDs still exist, but label them deprecated and point at Flash — the same guidance Models already uses.

Suggested table note (wording can match Models verbatim):

```text
`eleven_turbo_v2_5` / `eleven_turbo_v2` are deprecated. Prefer `eleven_flash_v2_5` / `eleven_flash_v2`
(same quality class, lower average latency).
```

Alternatively drop Turbo from the "use these" table and add a one-line deprecated footnote so old cookbooks still grep.

**Why it matters:** the [ElevenAPI quickstart](https://elevenlabs.io/docs/eleven-api/quickstart) tells developers to `npx skills add elevenlabs/skills --skill text-to-speech` first. The skill table is then the first model list they copy.

## 2. Align Scribe keyterm cap in `speech-to-text/SKILL.md`

**File:** `speech-to-text/SKILL.md` (Keyterm Prompting).

**Change:** Models says "up to 1000 terms"; the skill says "up to 100 terms". Either update the skill to 1000 or document why 100 is a different limit.

## 3. Weekly drift check (prototype in this repo)

`scripts/skills_model_drift.py` plus `eleven_demo.skills_drift` implement a small, testable **line-level** heuristic (not a table parser):

- Turbo IDs on a TTS skill row without a same-line deprecation note, while Models lists them under Deprecated. The script exits 1 when a Turbo row in the skill table lacks a deprecation note.
- Keyterm cap integer mismatch between the STT skill and Models (first `up to N terms` near the word `keyterm`).

A GitHub Action on `elevenlabs/skills` could run the same comparison against `https://elevenlabs.io/docs/overview/models.md` and open an issue when it fails. Unit tests in this lab mock the markdown (no network in CI).

## Source-of-truth order we used

Official docs → installed SDK → `elevenlabs/skills` → local cookbook. See [Learning experience](../product/learning-experience.md).
