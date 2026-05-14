# Open WebUI Notes Bug — Debug Session

## Environment

- OS: Windows 11 + WSL2 (Ubuntu)
- Open WebUI: 0.9.4 (pip installed via `pip install open-webui --user --break-system-packages`)
- Python: 3.12
- Database: SQLite at `/home/yanmuu/.local/lib/python3.12/site-packages/open_webui/data/webui.db`
- Backend: Hermes Gateway (port 8642) as OpenAI-compatible API provider
- Frontend: SvelteKit SPA compiled to `frontend/_app/immutable/`

## Bug 1: Creating notes fails with "'is_pinned' is an invalid keyword argument for Note"

### Error (from Open WebUI stderr/log)

```
TypeError: 'is_pinned' is an invalid keyword argument for Note
...
File "open_webui/models/notes.py", line 143, in insert_new_note
    new_note = Note(**note.model_dump(exclude={'access_grants'}))
```

### Root cause

Two tables + two models diverge:

- **`Note`** (SQLAlchemy model, maps to `note` DB table): columns are `id, user_id, title, data, meta, created_at, updated_at` — NO `is_pinned` column
- **`NoteModel`** (Pydantic model, API schema): has `is_pinned: Optional[bool] = False` (line 46)

The `NoteModel.is_pinned` was added to support the "pinned notes" feature, but was removed from the DB column when the `pinned_note` table was introduced as a separate relation. The Alembic migration `e1f2a3b4c5d6` originally added `is_pinned` to the `note` table; a later migration `4de81c2a3af1` moved this to a separate `pinned_note` table and DROPPED the column.

However, `NoteModel` kept `is_pinned` for the API layer (computed at query time from the `pinned_note` table via `note.id in pinned_note_ids`). When inserting a new note, the code at line 143 dumps the Pydantic model and passes `is_pinned` to the SQLAlchemy `Note()` constructor — which doesn't have the column.

### Fix

Patch line 143 in `open_webui/models/notes.py`:

```python
# BEFORE:
new_note = Note(**note.model_dump(exclude={'access_grants'}))
# AFTER:
new_note = Note(**note.model_dump(exclude={'access_grants', 'is_pinned'}))
```

### Verification

```bash
python3 << 'PYEOF'
import sqlite3, uuid, time

db_path = "/home/yanmuu/.local/lib/python3.12/site-packages/open_webui/data/webui.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

user_id = "8652ec94-a656-42ad-8789-30671f744a4d"
note_id = str(uuid.uuid4())
now = int(time.time_ns())

cur.execute("""
    INSERT INTO note (id, user_id, title, data, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
""", (note_id, user_id, "test", '{"content":{"md":"hello"}}', now, now))
conn.commit()
print("Insert OK")

cur.execute("DELETE FROM note WHERE id=?", (note_id,))
conn.commit()
conn.close()
PYEOF
```

After fixing, restart Open WebUI. The fix takes effect on process restart (Python recompiles `.py` modules).

### API test (requires auth token)

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"YOUR_EMAIL","password":"YOUR_PASSWORD"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

curl -s -X POST http://127.0.0.1:8080/api/v1/notes/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"API Test Note","data":{"content":{"md":"Created via API"}}}'
```

## Bug 2: Sidebar "New Note" opens chat page instead of note editor

Even after the backend fix (Bug 1), clicking the "New Note" button in the sidebar or Workspace leads to a new chat page. This is a **frontend SPA routing issue**, not a backend issue.

### Code path (from compiled JS)

The sidebar notes section in `nodes/2.DCxAWxDL.js`:

```javascript
onAdd: async() => {
    const lt = await Fc("New Note");  // createNewNote API call
    lt && pa(`/notes/${lt.id}`);       // navigate to /notes/{id}
}
```

`Fc` maps to the `createNewNote` async function which POSTs to `/api/v1/notes/create`. The SPA route `/notes/[id]` is supposed to render the note editor.

### Problem

The SPA has routes defined:
- `/notes` — ? (list or new)
- `/notes/new` — create template
- `/notes/[id]` — view/edit note

But in the pip-installed 0.9.4 build, the SvelteKit app may not have the `+page.svelte` for notes compiled in properly. The catch-all route renders the chat interface instead.

### Workaround

Use the API directly (see Bug 1 above) — notes can be created and queried, just the SPA frontend doesn't render them. This is an upstream packaging issue.

## Database Schema Reference

```sql
CREATE TABLE "note" (
    id TEXT NOT NULL,
    user_id TEXT,
    title TEXT,
    data JSON,
    meta JSON,
    created_at BIGINT,
    updated_at BIGINT,
    PRIMARY KEY (id),
    UNIQUE (id)
);

CREATE TABLE "pinned_note" (
    id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    note_id TEXT NOT NULL REFERENCES note(id) ON DELETE CASCADE,
    created_at BIGINT NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (user_id, note_id)
);
```

NoteModel (Pydantic) fields: `id, user_id, title, data, meta, is_pinned, access_grants, created_at, updated_at`

## Migration History

The `migratehistory` table had 18 entries (001–018). Missing alembic migrations that would have added/dropped `is_pinned`:

| Migration | Status | Description |
|-----------|--------|-------------|
| `e1f2a3b4c5d6_add_is_pinned_to_note` | ❌ Not applied | Would add `is_pinned` boolean column |
| `4de81c2a3af1_add_pinned_note_table` | ❌ Not applied | Creates `pinned_note` table, migrates data from `is_pinned`, then drops `is_pinned` column |

The migration chain used `peewee_migrate` (not Alembic) for the schema, which may explain why Alembic migrations under `migrations/versions/` were never run.
