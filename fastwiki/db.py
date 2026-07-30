from __future__ import annotations
import json, os, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path

def now() -> str: return datetime.now(timezone.utc).isoformat()
def conn():
    path = Path(os.getenv("FASTWIKI_DB", "data/fastwiki.sqlite"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db
def rows(sql, args=()):
    with conn() as db: return [dict(r) for r in db.execute(sql, args).fetchall()]
def row(sql, args=()):
    with conn() as db:
        found = db.execute(sql, args).fetchone()
        return dict(found) if found else None
def execute(sql, args=()):
    with conn() as db:
        cur = db.execute(sql, args); db.commit(); return cur.lastrowid

SCHEMA = """
CREATE TABLE IF NOT EXISTS orgs(id TEXT PRIMARY KEY,name TEXT NOT NULL,logo_url TEXT);
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT NOT NULL,name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS memberships(org_id TEXT,user_id TEXT,role TEXT NOT NULL,PRIMARY KEY(org_id,user_id));
CREATE TABLE IF NOT EXISTS invitations(id INTEGER PRIMARY KEY,org_id TEXT,email TEXT,role TEXT,token TEXT UNIQUE,status TEXT DEFAULT 'pending',created_at TEXT);
CREATE TABLE IF NOT EXISTS spaces(id INTEGER PRIMARY KEY,org_id TEXT NOT NULL,name TEXT NOT NULL,slug TEXT NOT NULL,description TEXT DEFAULT '',visibility TEXT DEFAULT 'org',comments_mode TEXT DEFAULT 'both',created_at TEXT,UNIQUE(org_id,slug));
CREATE TABLE IF NOT EXISTS pages(id INTEGER PRIMARY KEY,org_id TEXT NOT NULL,space_id INTEGER NOT NULL,parent_id INTEGER,title TEXT NOT NULL,slug TEXT NOT NULL,content_json TEXT NOT NULL,markdown TEXT DEFAULT '',plain_text TEXT DEFAULT '',version INTEGER DEFAULT 1,status TEXT DEFAULT 'published',created_by TEXT,updated_by TEXT,created_at TEXT,updated_at TEXT,deleted_at TEXT);
CREATE TABLE IF NOT EXISTS page_versions(id INTEGER PRIMARY KEY,page_id INTEGER,org_id TEXT,version INTEGER,content_json TEXT,markdown TEXT,title TEXT,created_by TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS comments(id INTEGER PRIMARY KEY,page_id INTEGER,org_id TEXT,user_id TEXT,body TEXT,kind TEXT DEFAULT 'page',anchor_json TEXT DEFAULT '{}',resolved_at TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS attachments(id INTEGER PRIMARY KEY,page_id INTEGER,org_id TEXT,name TEXT,storage_key TEXT,content_type TEXT,size INTEGER,created_by TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS embeds(id INTEGER PRIMARY KEY,page_id INTEGER,org_id TEXT,product TEXT,title TEXT,url TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS favourites(org_id TEXT,user_id TEXT,page_id INTEGER,PRIMARY KEY(org_id,user_id,page_id));
"""

def init():
    with conn() as db: db.executescript(SCHEMA)

def provision(who: dict):
    with conn() as db:
        db.execute("INSERT OR IGNORE INTO orgs VALUES(?,?,NULL)", (who["org_id"], who.get("org_name") or "Workspace"))
        db.execute("INSERT INTO users VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET email=excluded.email,name=excluded.name", (who["sub"],who["email"],who.get("name") or who["email"].split("@")[0]))
        db.execute("INSERT OR REPLACE INTO memberships VALUES(?,?,?)",(who["org_id"],who["sub"],who.get("role","member")))
        if not db.execute("SELECT 1 FROM spaces WHERE org_id=?",(who["org_id"],)).fetchone():
            ts=now(); sid=db.execute("INSERT INTO spaces(org_id,name,slug,description,created_at) VALUES(?,?,?,?,?)",(who["org_id"],"Company handbook","handbook","Shared knowledge for the whole team",ts)).lastrowid
            content={"type":"doc","content":[{"type":"heading","attrs":{"level":1},"content":[{"type":"text","text":"Welcome to FastWiki"}]},{"type":"paragraph","content":[{"type":"text","text":"Capture decisions, processes, and ideas in one calm workspace."}]}]}
            db.execute("INSERT INTO pages(org_id,space_id,title,slug,content_json,markdown,plain_text,created_by,updated_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(who["org_id"],sid,"Welcome","welcome",json.dumps(content),"# Welcome to FastWiki\n\nCapture decisions, processes, and ideas.","Welcome to FastWiki Capture decisions processes and ideas",who["sub"],who["sub"],ts,ts))
        db.commit()

def spaces(org): return rows("SELECT * FROM spaces WHERE org_id=? ORDER BY name",(org,))
def pages(org, include_deleted=False):
    where="" if include_deleted else "AND deleted_at IS NULL"
    return rows(f"SELECT p.*,s.name space_name FROM pages p JOIN spaces s ON s.id=p.space_id WHERE p.org_id=? {where} ORDER BY p.parent_id IS NOT NULL,p.title",(org,))
def page(org,pid): return row("SELECT p.*,s.name space_name,s.comments_mode FROM pages p JOIN spaces s ON s.id=p.space_id WHERE p.org_id=? AND p.id=?",(org,pid))
def create_space(who,name,description="",visibility="org",comments_mode="both"):
    slug=re.sub(r"[^a-z0-9]+","-",name.lower()).strip("-") or "space"
    return execute("INSERT INTO spaces(org_id,name,slug,description,visibility,comments_mode,created_at) VALUES(?,?,?,?,?,?,?)",(who["org_id"],name,slug,description,visibility,comments_mode,now()))
def create_page(who,space_id,title,parent_id=None):
    allowed=row("SELECT id FROM spaces WHERE org_id=? AND id=?",(who["org_id"],space_id))
    if not allowed: raise ValueError("space")
    empty=json.dumps({"type":"doc","content":[{"type":"paragraph"}]})
    slug=re.sub(r"[^a-z0-9]+","-",title.lower()).strip("-") or "untitled"
    ts=now()
    return execute("INSERT INTO pages(org_id,space_id,parent_id,title,slug,content_json,created_by,updated_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(who["org_id"],space_id,parent_id,title,slug,empty,who["sub"],who["sub"],ts,ts))
def save_page(who,pid,title,content_json,markdown,version):
    current=page(who["org_id"],pid)
    if not current or current["deleted_at"]: return None
    if current["version"] != version: return {"conflict":True,"version":current["version"]}
    try: parsed=json.loads(content_json)
    except json.JSONDecodeError: raise ValueError("content_json")
    text=" ".join(re.findall(r'"text"\\s*:\\s*"([^"]*)"',content_json))
    with conn() as db:
        db.execute("INSERT INTO page_versions(page_id,org_id,version,content_json,markdown,title,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)",(pid,who["org_id"],current["version"],current["content_json"],current["markdown"],current["title"],who["sub"],now()))
        db.execute("UPDATE pages SET title=?,content_json=?,markdown=?,plain_text=?,version=version+1,updated_by=?,updated_at=? WHERE org_id=? AND id=? AND version=?",(title,json.dumps(parsed),markdown,text,who["sub"],now(),who["org_id"],pid,version))
        db.commit()
    return page(who["org_id"],pid)
def search(org,q):
    like=f"%{q}%"
    return rows("SELECT p.id,p.title,p.plain_text,s.name space_name,p.updated_at FROM pages p JOIN spaces s ON s.id=p.space_id WHERE p.org_id=? AND p.deleted_at IS NULL AND (p.title LIKE ? OR p.plain_text LIKE ?) ORDER BY p.updated_at DESC LIMIT 30",(org,like,like))
def trash(who,pid): execute("UPDATE pages SET deleted_at=? WHERE org_id=? AND id=?",(now(),who["org_id"],pid))
def restore(who,pid): execute("UPDATE pages SET deleted_at=NULL WHERE org_id=? AND id=?",(who["org_id"],pid))
def comments(org,pid): return rows("SELECT c.*,u.name user_name FROM comments c JOIN users u ON u.id=c.user_id WHERE c.org_id=? AND c.page_id=? ORDER BY c.id",(org,pid))
def add_comment(who,pid,body,kind="page",anchor_json="{}"):
    target=page(who["org_id"],pid)
    if not target or target["comments_mode"]=="off" or (target["comments_mode"]=="page" and kind=="inline") or (target["comments_mode"]=="inline" and kind=="page"): raise ValueError("comments disabled")
    return execute("INSERT INTO comments(page_id,org_id,user_id,body,kind,anchor_json,created_at) VALUES(?,?,?,?,?,?,?)",(pid,who["org_id"],who["sub"],body,kind,anchor_json,now()))
def add_embed(who,pid,product,title,url):
    if not page(who["org_id"],pid): raise ValueError("page")
    return execute("INSERT INTO embeds(page_id,org_id,product,title,url,created_at) VALUES(?,?,?,?,?,?)",(pid,who["org_id"],product,title,url,now()))
def embeds(org,pid): return rows("SELECT * FROM embeds WHERE org_id=? AND page_id=? ORDER BY id DESC",(org,pid))
def add_attachment(who,pid,name,key,ctype,size):
    if not page(who["org_id"],pid): raise ValueError("page")
    return execute("INSERT INTO attachments(page_id,org_id,name,storage_key,content_type,size,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)",(pid,who["org_id"],name,key,ctype,size,who["sub"],now()))
def attachment(org,aid): return row("SELECT * FROM attachments WHERE org_id=? AND id=?",(org,aid))
def attachments(org,pid): return rows("SELECT * FROM attachments WHERE org_id=? AND page_id=? ORDER BY id DESC",(org,pid))

init()
