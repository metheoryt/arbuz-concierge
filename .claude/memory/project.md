# arbuz-concierge — project memory

<!-- KB refreshed against 1a6b886 on 2026-09-12 -->

Durable, repo-specific facts an agent would otherwise have to rediscover by
reading the whole tree. This repo has no `CLAUDE.md`, no `README.md` and no
`docs/` — this file is the only written account of it.

## Scraping arbuz.kz
- **`app/arbuz/api.py` calls `login()` at module import time, at the bottom of the file.** Importing anything under `app.arbuz` — which `app/loader.py` and therefore the `arbuz load` CLI command both do — fires two live requests at arbuz.kz before any of your code runs. So an import is never free, it fails with no useful traceback when the site is unreachable, and unit-testing anything downstream of the loader means faking that module.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **The catalog tree and the API credentials are scraped out of the homepage HTML with regexes, not fetched from an API.** `login()` reads `window.platformConfiguration` for the desktop consumer name+key and posts them to `/api/v1/auth/token`; `get_catalog_tree_json()` reads `window.siteCatalogTree = Object.values(…)`. A front-end redesign therefore breaks this repo with `ValueError: Failed to retrieve platform configuration` / `…catalog tree` — a plain `ValueError`, never an HTTP status, so do not go looking for a 4xx.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **The loader is deliberately slow, and the sleeps are politeness toward arbuz.kz, not latency padding.** Two seconds between categories and between products-of-a-category, four seconds between product pages, forty products per page, on top of an `httpx-retries` policy of three attempts with backoff on 429/500/502/503/504. A full `arbuz load` is an hours-long job by design; do not "optimise" the sleeps away.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **Products are imported for leaf categories only** — `select(Category).where(~Category.children.any())` — because branch categories carry no products of their own. The leaves are walked oldest-`updated_at`-first, so an interrupted load resumes roughly where it stopped rather than restarting at the top.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **A 404 is a normal outcome on two paths and is swallowed, not raised**: a category whose info endpoint 404s is skipped, and a catalog whose products endpoint 404s is treated as "no products". Any other `HTTPStatusError` propagates and aborts the run.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **Upstream sends numbers as comma-decimal strings and free text where a number belongs, so the schemas repair before validating.** `parse_comma_float` turns `"1,5"` into `1.5` and returns `None` for anything unparseable rather than raising; the rating's `reviews` field arrives as `"12 оценок"` and is split on whitespace; `characteristics: null` is normalised to `[]`; `storage_conditions` / `information` / `ingredients` arrive as HTML and are run through html2text. Both schema models are `extra="allow"` with a camelCase alias generator, so new upstream fields land harmlessly.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **Nutrition totals above 100 g per 100 g are an upstream data bug and are dropped, in two independent places** — `Product.text_embedding()` and `search_products()` both refuse to emit nutrition when protein+fat+carbs exceeds 100. Keep the two in step if either changes.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **A product's category is overwritten to the catalog it was found in** (`ps.catalog_id = cat.id` in `get_catalog_products`), deliberately ignoring what the payload claims, and its `sort_pos` is the position across the whole paginated walk, not within the page.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->

## Embeddings and vector search
- **1536 dimensions are hard-wired to `text-embedding-3-small` in two places** — the `Vector(1536)` column on `product_embedding` and the model name in `app/gpt/embeddings.py`. Switching embedding models is an alembic migration plus a full re-embed, never a one-line change.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **What gets embedded is a rendered Russian document, not the product name.** `Product.text_embedding()` composes name, brand, country, the full `parent > child > leaf` category breadcrumbs with each position, features, ingredients, nutrition and rating. `Category.text_embedding()` recurses up the parent chain to build that breadcrumb. Changing either changes what every stored vector means, so a re-embed has to follow.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **The similarity search interpolates the query vector into raw SQL** (`text(f"vector <=> {format_vector(emb.embedding)}")`) rather than binding it, and **no index is created on that column by any migration or initdb script** — so every search is a sequential scan over the whole embedding table ordered by cosine distance. The vchord extension is installed and unused for indexing.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **Only products with `is_available` true are searchable**, and the per-query result budget is `max_results // len(embs)` — so an agent that fires many sub-queries gets very few hits from each one. Results are de-duplicated through a set before the rows are loaded.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->

## Database and environment
- **The database is `tensorchord/vchord-postgres`, and the two `initdb/` scripts only ever run against an empty volume** — they create the `vchord` extension and an empty `marvin` schema. A database that already exists never sees them, so a missing extension on an older volume has to be created by hand.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **`compose.yml` publishes postgres on host port 5435, but `.dist.env`'s `POSTGRES_URL` names no port at all** and therefore resolves to the default 5432. Anyone copying the example file onto the composed database has to add the port.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **The engine is synchronous** — `create_engine` + `sessionmaker`, no async session anywhere — even though `asyncpg` is a declared dependency. Nothing imports asyncpg; the DSN in the example env is `postgresql+psycopg`.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **`alembic/env.py` reads `DATABASE_URL` into a local that is never used**, then unconditionally overrides `sqlalchemy.url` from `settings.postgres_url`. The `.env` file is the only thing that decides which database a migration hits.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->

## What is wired and what is not
- **The `arbuz` CLI exposes exactly one command, `load`**, which runs categories then products. **Embedding generation is not wired to it**: `app/embedder.py:generate_embeddings()` has no caller anywhere in the repo, so vectors only exist if someone invokes it by hand. A freshly loaded database therefore returns nothing from the product search and looks broken.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **Several modules are scratch, not live paths — and one of them spends money merely by being imported.** `app/llm.py` runs two `marvin` agent calls and a `print` at module scope, so importing it costs OpenAI calls; `app/gpt/memory.py` builds a `PostgresMemory` provider nothing consumes (the `marvin` schema `initdb/marvin.sql` creates exists for it); `app/db/models/tg_chat.py` is entirely commented out and is not exported from `models/__init__.py`. The live entry points are `cli.py` and the `__main__` block in `app/gpt/productologist.py`.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **The agent layer is `marvin` on `openai:gpt-4o-mini`, and the whole prompt surface is Russian** — agent instructions, pydantic field descriptions and the interactive prompt alike. The productologist's own instructions tell the model that its search queries become `text-embedding-3-small` vectors and must be short keyword phrases; that coupling between prompt text and retrieval is deliberate.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
- **Style is enforced by ruff only — there is no test suite and no type checker.** Line length 120, target `py314`, a wide `select` with `ANN` and `PL` deliberately commented out, and a pre-commit hook running `ruff-check --fix` plus `ruff-format`. The project requires Python >= 3.14.
  <!-- src: arbuz-concierge 1a6b886 | 2026-09-12 -->
