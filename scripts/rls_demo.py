"""
RLS demo: what can the public anon key do?
Usage: python scripts/rls_demo.py
"""
import json
import uuid

from supabase import create_client

with open('config.public.json') as f:
    public = json.load(f)

# Connect with the ANON key (not the service key!) -- same as any website visitor
client = create_client(public['SUPABASE_URL'], public['SUPABASE_ANON_KEY'])


def attempt(label, fn):
    try:
        result = fn()
        print(f"  ✅ {label}: allowed ({len(result.data)} rows)")
    except Exception as e:
        msg = getattr(e, 'message', None) or str(e)
        print(f"  🔒 {label}: BLOCKED -> {msg}")


print("page_views (public policies):")
attempt("read", lambda: client.table('page_views').select('*').limit(5).execute())
attempt("write", lambda: client.table('page_views').insert(
    {'page_url': 'rls_demo.py', 'user_agent': 'rls demo'}).execute())

print("\nsentence_embeddings (authenticated-read only):")
attempt("read", lambda: client.table('sentence_embeddings').select('*').limit(5).execute())
attempt("write", lambda: client.table('sentence_embeddings').insert(
    {'talk_id': str(uuid.uuid4()), 'title': 'Fake talk', 'text': 'Injected by anon'}).execute())
