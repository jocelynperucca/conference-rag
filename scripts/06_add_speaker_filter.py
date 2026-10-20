"""
Step 6: Add Speaker Filter (custom feature)
============================================
Adds three SQL functions so RAG can be limited to one speaker's talks:

  speaker_key(raw)                 -> 'By Elder Henry B. Eyring' -> 'Henry B. Eyring'
  list_speakers()                  -> every speaker + talk count, for the dropdown
  match_sentences_by_speaker(...)  -> semantic search within one speaker's talks

The raw `speaker` column is never modified -- names are cleaned when read.
(Updating 25k rows would re-insert every vector into the HNSW index.)

Usage:
    python scripts/06_add_speaker_filter.py
"""

import json
import sys

import requests

with open('config.secret.json', 'r') as f:
    secrets = json.load(f)

SPEAKER_FILTER_SQL = r"""
-- ============================================================
-- 1. speaker_key(): turn a raw speaker string into a clean name
-- ============================================================
-- 'By President Henry B. Eyring'  ->  'Henry B. Eyring'
-- 'By Elder Henry B. Eyring'      ->  'Henry B. Eyring'   (same person!)
--
-- replace(..., chr(160), ' ')  : non-breaking space -> normal space
-- regexp_replace(..., '^By\s+((President|...)\s+)?', '')
--     ^            start of the string
--     By\s+        "By" followed by spaces
--     ( ... )?     optionally, one title followed by spaces
-- IMMUTABLE tells Postgres: same input always gives the same output.
CREATE OR REPLACE FUNCTION speaker_key(raw text)
RETURNS text
LANGUAGE sql IMMUTABLE
AS $$
  SELECT trim(regexp_replace(
    replace(raw, chr(160), ' '),
    '^By\s+((President|Elder|Sister|Bishop|Brother)\s+)?',
    ''
  ));
$$;

-- ============================================================
-- 2. list_speakers(): one row per person, for the dropdown
-- ============================================================
-- Should return rows like:  ('Russell M. Nelson', 27), ('Dallin H. Oaks', 17), ...
CREATE OR REPLACE FUNCTION list_speakers()
RETURNS TABLE (name text, talk_count bigint)
LANGUAGE sql STABLE
AS $$
  SELECT
    speaker_key(speaker) AS name,
    count(DISTINCT talk_id) AS talk_count   -- talks, not sentences!
  FROM sentence_embeddings
  WHERE speaker LIKE 'By %'
  GROUP BY 1
  ORDER BY talk_count DESC, name;
$$;

-- ============================================================
-- 3. match_sentences_by_speaker(): semantic search, one speaker only
-- ============================================================
-- Same output columns as match_sentences(), so app.js can treat the
-- results identically.
--
-- WHY THE CTE?  The HNSW index finds the ~40 nearest sentences in the WHOLE
-- table and only THEN applies a WHERE filter. If none of those 40 are by
-- our speaker -> zero results ("post-filtering problem").
-- So we filter FIRST into speaker_rows (a few hundred rows), then compare
-- every one of them exactly. MATERIALIZED forces Postgres to do it in
-- that order.
CREATE OR REPLACE FUNCTION match_sentences_by_speaker(
  query_embedding vector(1536),
  speaker_name text,
  match_count int DEFAULT 20
)
RETURNS TABLE (
  id uuid,
  talk_id uuid,
  title text,
  speaker text,
  text text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  WITH speaker_rows AS MATERIALIZED (
    SELECT *
    FROM sentence_embeddings
    
    WHERE speaker like 'By %' AND speaker_key(speaker) = speaker_name
  )
  SELECT
    speaker_rows.id,
    speaker_rows.talk_id,
    speaker_rows.title,
    speaker_rows.speaker,
    speaker_rows.text,
    1 - (speaker_rows.embedding <=> query_embedding) AS similarity
  FROM speaker_rows
  -- TODO E: Closest first, and only match_count rows.
  --   Look at match_sentences() in scripts/01_create_schema.py -- it's the
  --   same two lines, just reading from speaker_rows.
  ORDER BY speaker_rows.embedding <=> query_embedding
  LIMIT match_count;
$$;
"""


def run_sql(sql):
    url = f"https://api.supabase.com/v1/projects/{secrets['SUPABASE_PROJECT_REF']}/database/query"
    headers = {"Authorization": f"Bearer {secrets['SUPABASE_ACCESS_TOKEN']}"}
    resp = requests.post(url, headers=headers, json={"query": sql}, timeout=120)
    if resp.status_code not in (200, 201):
        print(f"❌ SQL failed: {resp.status_code}")
        print(resp.text[:500])
        sys.exit(1)
    return resp.json()


if __name__ == '__main__':
    print("=" * 60)
    print("Adding speaker filter functions")
    print("=" * 60)
    run_sql(SPEAKER_FILTER_SQL)
    print("✅ Functions created")

    speakers = run_sql("SELECT * FROM list_speakers() LIMIT 5")
    print(f"\nTop speakers:")
    for s in speakers:
        print(f"   {s['talk_count']:>3} talks  {s['name']}")
    print(f"\n✅ Speaker filter ready! Next: add the dropdown in app.js")
