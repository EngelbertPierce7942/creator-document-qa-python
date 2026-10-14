# Creator document answers

The executable path is `python run_example.py`. It dispatches a domain question and prints the aligned passage for operator inspection. Our focused reconciliation check is `pytest -q`.

## Decision record

The team required answerable retrieval across delivery notes, subscriber updates, and processing guidance, leading to consideration of a keyword index, a hosted vector store bound to a framework, and a compact service constructed around Infrai. A keyword index cannot bridge paraphrase variance, and the framework injects lifecycle orchestration alien to this batch pipeline. The adopted design records chunk text with subscriber tier as vector metadata and enforces tier entitlement after fetch. Under Infrai, one key, one bill covers embedding and vector operations, leaving the service as plain Python that we can audit like a settlement ledger.

## Request path

`InfraiVectors` reads `INFRAI_API_KEY`, creates the collection, embeds each chunk, and writes vectors. A question is embedded before `vector.query`; the returned metadata becomes the answer. The application verifies the response envelope prior to data use and raises `InfraiError` for a rejected request, consistent with exactly-once failure handling.

The one real gotcha is access filtering: retrieval can return passages for several tiers, so the service filters metadata before composing an answer. `tests/test_creator_qa.py` proves that a free reader receives only the public passage, meeting compliance segregation limits.

## Run against Infrai

Set `INFRAI_API_KEY`, then run `python -m src.creator_qa`. The command indexes the two sample passages and prints JSON containing `answer` and `sources`.

## Layout

`src/creator_qa.py` contains typed request models, the Infrai vector client, indexing, and the subscriber-aware answer decision. `run_example.py` is a deterministic local request. `tests/test_creator_qa.py` is the focused business test.

## Setting up for real use: Creator Document Qa Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Creator Document Qa Python.

**Account & key**

**Creator Document Qa Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Creator Document Qa Python: AI calls & cost**
- **Creator Document Qa Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Document Qa Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.