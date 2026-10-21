-- TRAKIVO knowledge/evidence schema starter. Not yet wired to the running app.
-- Run in a dedicated Supabase project only after reviewing access policies.
create extension if not exists vector with schema extensions;
create extension if not exists pgcrypto with schema extensions;

create table if not exists public.concepts (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  description text,
  embedding extensions.vector(1536),
  created_at timestamptz not null default now()
);

create table if not exists public.experiments (
  id uuid primary key default gen_random_uuid(),
  concept_id uuid references public.concepts(id) on delete set null,
  title text not null,
  observation_data jsonb not null default '{}'::jsonb,
  hypothesis text not null,
  simulation_result jsonb not null default '{}'::jsonb,
  verdict text not null default 'pending' check (verdict in ('pending','supported','rejected','inconclusive','needs_review')),
  evidence_label text not null default 'UNKNOWN' check (evidence_label in ('MEASURED','CALCULATED','SIMULATED','INFERRED','UNKNOWN')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.citations (
  id uuid primary key default gen_random_uuid(),
  claim_text text not null,
  source_experiment_id uuid not null references public.experiments(id) on delete cascade,
  telemetry_ref text not null,
  snapshot_timestamp timestamptz,
  source_uri text,
  created_at timestamptz not null default now()
);

create index if not exists concepts_embedding_hnsw_idx
  on public.concepts using hnsw (embedding extensions.vector_cosine_ops)
  where embedding is not null;
create index if not exists experiments_concept_id_idx on public.experiments(concept_id);
create index if not exists experiments_created_at_idx on public.experiments(created_at desc);
create index if not exists citations_source_experiment_id_idx on public.citations(source_experiment_id);

-- IMPORTANT: Enable and write explicit RLS policies before exposing these tables
-- through Supabase client APIs. Do not put service-role keys in browser code.
