-- Guideline RAG vector store — ADOPT item (docs/tech_radar.md, v0.6.1).
--
-- Executed once by the postgres image's initdb on the FIRST boot of the
-- rag-vector-data volume. DORMANT until the GPU pilot flips
-- VECTOR_BACKEND=sbert on guideline-rag and points VECTOR_DB_URL here:
-- nothing writes or reads this schema before then. The embedding loader
-- (corpus chunks -> 384-d all-MiniLM-L6-v2 vectors) lands with that pilot;
-- shipping the schema now means the pilot is a flip + a loader, not
-- infrastructure work.
--
-- Scale assumption: hospital corpus < 100k chunks -> HNSW cosine gives
-- millisecond ANN inside the existing data tier (tech_radar verdict:
-- pgvector form; a dedicated vector DB waits for ~1M+ chunks).

CREATE EXTENSION IF NOT EXISTS vector;

-- One row per corpus section, mirroring the chunk contract of
-- services/guideline-rag/app/main.py:_load_corpus (corpus_id + section is
-- the natural key; content_sha makes re-syncs idempotent).
CREATE TABLE IF NOT EXISTS chunks (
  id          BIGSERIAL PRIMARY KEY,
  corpus_id   TEXT        NOT NULL,
  section     TEXT        NOT NULL,
  edition     TEXT        NOT NULL,
  title       TEXT        NOT NULL DEFAULT '',
  content     TEXT        NOT NULL,
  content_sha TEXT        NOT NULL,
  embedding   vector(384) NOT NULL,   -- all-MiniLM-L6-v2 dimensionality
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (corpus_id, section)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
  ON chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chunks_corpus_idx ON chunks (corpus_id);

-- Provenance for governance: which loader/model produced current contents,
-- and against which manifest revision. Append-only on purpose.
CREATE TABLE IF NOT EXISTS sync_log (
  id           BIGSERIAL PRIMARY KEY,
  loaded_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  model        TEXT        NOT NULL,
  chunks       INT         NOT NULL,
  manifest_sha TEXT        NOT NULL
);
