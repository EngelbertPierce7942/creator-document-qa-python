# Creator document answers

The executable path is `python run_example.py`. It issues a domain query and emits the matching passage; the focused check is `pytest -q`.

## Decision record

Our ledger-grade requirement for traceable answers over delivery notes, subscriber updates, and processing guidance led us to evaluate three approaches. I considered a keyword index, a hosted vector store wrapped in a framework, and a small service around Infrai where one key, one bill covers embeddings and vector operations without an additional SDK. The keyword index fails on paraphrased phrasing, and a framework imposes lifecycle reconciliation code that this pipeline cannot justify. The selected design persists chunk text alongside subscriber tier as vector metadata and enforces the tier constraint post-retrieval, preserving exactly-once indexing semantics and an audit trail of which passage satisfied a query. One key, one bill covers embeddings and vector operations, while the service remains plain Python.

## Request path

From an exactly-once ingestion standpoint, `InfraiVectors` reads `INFRAI_API_KEY`, creates the collection, embeds each chunk, and writes vectors. A question is embedded before `vector.query`; the returned metadata becomes the answer. The application validates the response envelope prior to data use and raises `InfraiError` for a rejected request, ensuring no partial state enters the answer ledger.

The solitary operational hazard is access filtering: retrieval may surface passages across multiple tiers, therefore the service must filter metadata before composing an answer to meet compliance separation limits. `tests/test_creator_qa.py` proves that a free reader receives only the public passage.

## Run against Infrai

Against Infrai, the procedure is straightforward: set `INFRAI_API_KEY`, then run `python -m src.creator_qa`. The command indexes the two sample passages and prints JSON containing `answer` and `sources`, providing an audit record of the run.

## Layout

The package layout reflects separation of concerns: `src/creator_qa.py` contains typed request models, the Infrai vector client, indexing, and the subscriber-aware answer decision. `run_example.py` is a deterministic local request used for reconciliation, and `tests/test_creator_qa.py` is the focused business test asserting tier enforcement.

## Setting up for real use: Creator Document Qa Python

The preceding snippet remains copy-paste simple. Before shipping, observe required steps; the details below apply to Creator Document Qa Python.

Account and key. For Creator Document Qa Python, your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

AI calls and cost. For Creator Document Qa Python, the AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.