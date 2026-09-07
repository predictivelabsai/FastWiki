import importlib, json, os
import base64, hashlib, hmac, time
from pathlib import Path
import pytest

@pytest.fixture()
def database(tmp_path,monkeypatch):
    monkeypatch.setenv("FASTWIKI_DB",str(tmp_path/"test.sqlite"))
    monkeypatch.setenv("FASTWIKI_UPLOAD_DIR",str(tmp_path/"uploads"))
    from fastwiki import db
    importlib.reload(db)
    a={"sub":"a","email":"a@example.com","name":"Alice","org_id":"org-a","org_name":"Alpha","role":"owner"}
    b={"sub":"b","email":"b@example.com","name":"Bob","org_id":"org-b","org_name":"Beta","role":"owner"}
    db.provision(a);db.provision(b)
    return db,a,b

def test_tenant_safe_pages(database):
    db,a,b=database
    aid=db.pages("org-a")[0]["id"]
    assert db.page("org-a",aid)
    assert db.page("org-b",aid) is None
    assert all(p["org_id"]=="org-b" for p in db.pages("org-b"))

def test_optimistic_lock_and_version_history(database):
    db,a,_=database
    page=db.pages("org-a")[0]
    body=json.dumps({"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"Updated"}]}]})
    saved=db.save_page(a,page["id"],"Updated",body,"Updated",1)
    assert saved["version"]==2
    assert db.save_page(a,page["id"],"Stale",body,"",1)=={"conflict":True,"version":2}
    assert db.row("SELECT count(*) n FROM page_versions WHERE page_id=?",(page["id"],))["n"]==1

def test_trash_is_recoverable_and_scoped(database):
    db,a,b=database
    pid=db.pages("org-a")[0]["id"]
    db.trash(b,pid)
    assert db.page("org-a",pid)["deleted_at"] is None
    db.trash(a,pid)
    assert db.page("org-a",pid)["deleted_at"]
    db.restore(a,pid)
    assert db.page("org-a",pid)["deleted_at"] is None

def test_comment_modes(database):
    db,a,_=database
    pid=db.pages("org-a")[0]["id"]
    db.add_comment(a,pid,"A useful note","inline")
    assert db.comments("org-a",pid)[0]["body"]=="A useful note"
    db.execute("UPDATE spaces SET comments_mode='page' WHERE org_id=?",("org-a",))
    with pytest.raises(ValueError):
        db.add_comment(a,pid,"No inline","inline")

def test_local_attachment_storage(database):
    db,a,_=database
    from fastwiki import storage
    key="org-a/1/example.txt"
    storage.put(key,b"hello","text/plain")
    assert storage.get(key)==b"hello"

def test_new_page_route_creates_page(database,monkeypatch):
    db,_,_=database
    monkeypatch.setenv("FASTWIKI_ENV","development")
    from app import app
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        assert client.get("/auth/dev").status_code==200
        before=len(db.pages("dev"))
        response=client.get("/pages/new",follow_redirects=False)

    assert response.status_code==303
    assert response.headers["location"].startswith("/pages/")
    assert len(db.pages("dev"))==before+1

def test_fastoffice_ticket_contract_and_replay_protection(monkeypatch):
    monkeypatch.setenv("FASTOFFICE_SSO_SECRET","shared-test-secret")
    from fastwiki import security
    security._seen.clear()
    payload={
        "sub":"1","email":"owner@example.com","name":"Owner",
        "org_id":"org-a","org_name":"Alpha","role":"owner",
        "aud":"wiki","exp":int(time.time())+60,"jti":"single-use-ticket",
    }
    encoded=base64.urlsafe_b64encode(
        json.dumps(payload,separators=(",",":")).encode()
    ).decode().rstrip("=")
    signature=hmac.new(
        b"shared-test-secret",encoded.encode(),hashlib.sha256
    ).hexdigest()
    ticket=f"{encoded}.{signature}"
    assert security.verify_suite_ticket(ticket)["email"]=="owner@example.com"
    assert security.verify_suite_ticket(ticket) is None
