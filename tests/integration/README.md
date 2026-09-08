# Integration tests

Scenario simulate cassettes use VCR ``match_on`` that includes the HTTP **body**, so multiple
``simulate`` requests to the same path do not replay the wrong conversation turn.

- **VCR replay** (committed `cassettes/*.yaml`): no live ElevenLabs/OpenAI traffic for matched HTTP exchanges. When `ELEVENLABS_API_KEY` is unset, `tests/conftest.py` sets `xi-ci-placeholder` so `Settings` can load; cassette-backed tests replay, tests without a cassette skip.
- **Recording** (missing cassette + real keys): **consumes API credits**. Prefer doing this on a developer machine, then commit sanitized YAML (headers with secrets are filtered by `@pytest.mark.vcr`).

## Record scenario + vendor cassettes

From the repo root, with a complete `.env`:

```bash
uv run python scripts/record_integration_cassettes.py --provision
```

`--provision` upserts the three demo agents when `DEMO_AGENT_ID_*` are unset. You need `DEFAULT_PT_VOICE_ID` before provisioning.

The script invokes pytest with ``--vcr-record=all`` so existing YAML is **re-recorded** from the live API (stale bodies are not replayed silently).

**Portability:** YAML files embed URLs and bodies from your account (including `agent_id` and `voice_id`). CI or teammates must use the **same** `DEMO_AGENT_ID_*` and `DEFAULT_PT_VOICE_ID` you used while recording, or delete the cassettes and re-record.

## Scenario simulate tests

`tests/integration/scenarios/` do **not** require `DEFAULT_PT_VOICE_ID` for `simulate` calls; they **do** require the corresponding `DEMO_AGENT_ID_*` when recording, or a committed cassette plus a placeholder API key for replay.

After migrating scenario agents to English-only (`language: en`) and new stable names (`*-en`), older scenario cassettes were removed; **re-record** with `scripts/record_integration_cassettes.py` when you have live agent ids and an API key.
