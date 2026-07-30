import importlib, json, os
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

