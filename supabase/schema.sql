-- Run in the Supabase SQL editor. Safe to re-run; also upgrades databases created by earlier versions.
-- Embedding size must match EMBED_DIM in rag/config.py (768; both OpenAI and Gemini models are truncated to it).

create extension if not exists vector;

create table if not exists documents (
  id           bigserial primary key,
  namespace    text        not null default 'public', -- 'public' = shared docs from ingest.py; 'session:<uuid>' = a visitor's uploads
  source       text        not null,          -- file name, e.g. "billing.md"
  chunk_index  int         not null,          -- position of the chunk within its source
  page         int,                            -- PDF page (1-based), null otherwise
  content      text        not null,
  content_hash text        not null,          -- sha256 of embedding model + embedded text; ingest skips unchanged chunks
  metadata     jsonb       not null default '{}'::jsonb,
  embedding    vector(768) not null,
  expires_at   timestamptz,                    -- uploads expire (24h); null = permanent
  created_at   timestamptz not null default now()
);

-- Upgrades for tables created before uploads existed.
alter table documents add column if not exists namespace text not null default 'public';
alter table documents add column if not exists expires_at timestamptz;
alter table documents drop constraint if exists documents_source_chunk_index_key;
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'documents_ns_source_chunk_key') then
    alter table documents add constraint documents_ns_source_chunk_key unique (namespace, source, chunk_index);
  end if;
end $$;

-- Keyword side of hybrid search: Postgres full-text index over the chunk text.
alter table documents
  add column if not exists fts tsvector generated always as (to_tsvector('english', content)) stored;

create index if not exists documents_embedding_hnsw on documents using hnsw (embedding vector_cosine_ops);
create index if not exists documents_fts_gin on documents using gin (fts);
create index if not exists documents_namespace_idx on documents (namespace);
create index if not exists documents_expires_idx on documents (expires_at) where expires_at is not null;

-- Dropped first because Postgres can't change a function's signature or return columns in place.
drop function if exists match_documents(vector, int);
drop function if exists match_documents(vector, int, text);
drop function if exists hybrid_search(text, vector, int, int);
drop function if exists hybrid_search(text, vector, int, int, text);

-- Pure vector search (RETRIEVAL_MODE=vector) over public docs + the caller's own uploads.
create or replace function match_documents(
  query_embedding vector(768),
  match_count     int  default 5,
  session_ns      text default null
)
returns table (
  id bigint, source text, chunk_index int, page int, content text, metadata jsonb,
  similarity float, score float, namespace text
)
language sql stable
as $$
  select
    d.id, d.source, d.chunk_index, d.page, d.content, d.metadata,
    1 - (d.embedding <=> query_embedding) as similarity,
    1 - (d.embedding <=> query_embedding) as score,
    d.namespace
  from documents d
  where (d.namespace = 'public' or d.namespace = session_ns)
    and (d.expires_at is null or d.expires_at > now())
  order by d.embedding <=> query_embedding
  limit match_count;
$$;

-- Hybrid search (RETRIEVAL_MODE=hybrid): vector + keyword rankings merged with Reciprocal Rank Fusion.
-- Keyword terms are OR-ed so a natural-language question doesn't need every word to match.
-- `similarity` is always the vector cosine score, so the "I don't know" threshold means the same thing in both modes.
create or replace function hybrid_search(
  query_text      text,
  query_embedding vector(768),
  match_count     int  default 5,
  rrf_k           int  default 60,
  session_ns      text default null
)
returns table (
  id bigint, source text, chunk_index int, page int, content text, metadata jsonb,
  similarity float, score float, namespace text
)
language sql stable
as $$
  with q as (
    select to_tsquery('english', replace(plainto_tsquery('english', query_text)::text, '&', '|')) as tsq
  ),
  visible as (
    select * from documents d
    where (d.namespace = 'public' or d.namespace = session_ns)
      and (d.expires_at is null or d.expires_at > now())
  ),
  vec as (
    select v.id, row_number() over (order by v.embedding <=> query_embedding) as rank
    from visible v
    order by v.embedding <=> query_embedding
    limit match_count * 4
  ),
  kw as (
    select v.id, row_number() over (order by ts_rank_cd(v.fts, q.tsq) desc) as rank
    from visible v, q
    where v.fts @@ q.tsq
    order by ts_rank_cd(v.fts, q.tsq) desc
    limit match_count * 4
  ),
  fused as (
    select coalesce(vec.id, kw.id) as id,
           coalesce(1.0 / (rrf_k + vec.rank), 0) + coalesce(1.0 / (rrf_k + kw.rank), 0) as score
    from vec full outer join kw on vec.id = kw.id
  )
  select d.id, d.source, d.chunk_index, d.page, d.content, d.metadata,
         1 - (d.embedding <=> query_embedding) as similarity,
         f.score,
         d.namespace
  from fused f
  join documents d on d.id = f.id
  order by f.score desc
  limit match_count;
$$;

-- The service-role key bypasses RLS; enable RLS so the anon key can't read or write the table.
alter table documents enable row level security;
