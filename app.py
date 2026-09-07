from __future__ import annotations
import json, mimetypes, os, secrets, uuid
from pathlib import Path
from dotenv import load_dotenv
from fasthtml.common import *
from fastwiki.seo import register_seo_routes
from starlette.responses import JSONResponse, RedirectResponse, Response
load_dotenv()
from fastwiki import db, storage, views
from fastwiki.api import api
from fastwiki.security import google_email_allowed, google_identity, verify_suite_ticket

GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID","")
GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET","")
GOOGLE_REDIRECT_URI=os.getenv("GOOGLE_REDIRECT_URI","")
_google_enabled=bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
_oauth=None
if _google_enabled:
    from authlib.integrations.starlette_client import OAuth
    _oauth=OAuth()
    _oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope":"openid email profile","prompt":"select_account"},
    )

app,rt=fast_app(secret_key=os.getenv("FASTWIKI_SECRET",secrets.token_hex(32)))
app.mount("/api",api)
def who(session): return session.get("identity")
def sign_in_path(): return "/auth/google" if _google_enabled else "/auth/suite"
def guard(session): return who(session) or RedirectResponse(sign_in_path(),status_code=303)
@rt("/")
def get(session):
    identity=who(session)
    if not identity:return views.landing(sign_in_path())
    pages=db.pages(identity["org_id"])
    return RedirectResponse(f"/pages/{pages[0]['id']}",status_code=303) if pages else RedirectResponse("/pages/new",status_code=303)
@rt("/health")
def get(): return JSONResponse({"status":"ok","product":"FastWiki","storage":storage.backend()})
@rt("/favicon.ico")
def get():
    return Response('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#4f46e5"/><path fill="white" d="M13 17h9l5 27 5-18 5 18 5-27h9l-10 31h-9l-5-16-5 16h-9Z"/></svg>',media_type="image/svg+xml")
@rt("/swagger.json")
def get(): return JSONResponse(api.openapi())
@rt("/openapi.json")
def get(): return JSONResponse(api.openapi())
@rt("/developers")
def get(): return RedirectResponse("/api/docs",status_code=307)
@rt("/auth/suite")
def get():
    return RedirectResponse(os.getenv("FASTOFFICE_URL","http://localhost:5020").rstrip("/")+"/launch/wiki",status_code=303)
@rt("/auth/suite/callback")
def get(session,ticket:str=""):
    identity=verify_suite_ticket(ticket)
    if not identity:return RedirectResponse("/?auth=invalid",status_code=303)
    db.provision(identity);session["identity"]={k:identity.get(k) for k in ("sub","email","name","org_id","org_name","role")}
    return RedirectResponse("/",status_code=303)
def google_redirect_uri(request):
    if GOOGLE_REDIRECT_URI:return GOOGLE_REDIRECT_URI
    host=request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    scheme=request.headers.get("x-forwarded-proto") or request.url.scheme
    return f"{scheme}://{host}/auth/google/callback"
@rt("/auth/google")
async def get(request):
    if not _google_enabled:return RedirectResponse("/",status_code=303)
    return await _oauth.google.authorize_redirect(request,google_redirect_uri(request))
@rt("/auth/google/callback")
async def get(request,session):
    if not _google_enabled:return RedirectResponse("/",status_code=303)
    try:token=await _oauth.google.authorize_access_token(request)
    except Exception:return RedirectResponse("/?auth=google_error",status_code=303)
    info=token.get("userinfo") or {}
    if not google_email_allowed(info):return RedirectResponse("/?auth=domain_denied",status_code=303)
    identity=google_identity(info)
    db.provision(identity);session["identity"]=identity
    return RedirectResponse("/",status_code=303)
@rt("/auth/dev")
def get(session,email:str="kaljuvee@gmail.com"):
    if os.getenv("FASTWIKI_ENV","development")=="production":return RedirectResponse("/",status_code=303)
    identity={"sub":email,"email":email,"name":"Julian Kaljuvee","org_id":"dev","org_name":"FastSME","role":"owner"}
    db.provision(identity);session["identity"]=identity
    return RedirectResponse("/",status_code=303)
@rt("/logout")
def get(session):session.clear();return RedirectResponse("/",status_code=303)
@rt("/pages/{pid}")
def get(session,pid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    current=db.page(identity["org_id"],pid)
    if not current or current["deleted_at"]:return Response("Page not found",status_code=404)
    return views.page_shell(identity,db.spaces(identity["org_id"]),db.pages(identity["org_id"]),current,db.comments(identity["org_id"],pid),db.attachments(identity["org_id"],pid),db.embeds(identity["org_id"],pid))
@rt("/pages/new")
def get(session):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    spaces=db.spaces(identity["org_id"])
    if not spaces:return RedirectResponse("/settings",status_code=303)
    pid=db.create_page(identity,spaces[0]["id"],"Untitled page")
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/pages/{pid}/save")
async def post(request,session,pid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return JSONResponse({"error":"unauthorized"},status_code=401)
    body=await request.json()
    try: result=db.save_page(identity,pid,body.get("title","Untitled"),body.get("content_json","{}"),body.get("markdown",""),int(body.get("version",0)))
    except (ValueError,TypeError):return JSONResponse({"error":"invalid content"},status_code=422)
    if not result:return JSONResponse({"error":"not found"},status_code=404)
    if result.get("conflict"):return JSONResponse(result,status_code=409)
    return JSONResponse({"id":pid,"version":result["version"],"updated_at":result["updated_at"]})
@rt("/pages/{pid}/trash")
def post(session,pid:int):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):db.trash(identity,pid)
    return RedirectResponse("/",status_code=303)
@rt("/pages/{pid}/restore")
def post(session,pid:int):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):db.restore(identity,pid)
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/pages/{pid}/comments")
def post(session,pid:int,body:str,kind:str="page"):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):
        try:db.add_comment(identity,pid,body,kind)
        except ValueError:pass
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/pages/{pid}/embeds")
def post(session,pid:int,product:str,title:str,url:str):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):db.add_embed(identity,pid,product,title,url)
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/pages/{pid}/attachments")
async def post(request,session,pid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    form=await request.form(); upload=form.get("file")
    if not upload:return RedirectResponse(f"/pages/{pid}",status_code=303)
    body=await upload.read();limit=int(os.getenv("FASTWIKI_MAX_UPLOAD_MB","20"))*1024*1024
    if len(body)>limit:return Response("File too large",status_code=413)
    safe=Path(upload.filename or "attachment").name.replace(" ","-")
    key=f"{identity['org_id']}/{pid}/{uuid.uuid4().hex}-{safe}"
    storage.put(key,body,upload.content_type or "application/octet-stream")
    db.add_attachment(identity,pid,safe,key,upload.content_type or "application/octet-stream",len(body))
    return RedirectResponse(f"/pages/{pid}",status_code=303)
@rt("/attachments/{aid}")
def get(session,aid:int):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    item=db.attachment(identity["org_id"],aid)
    if not item:return Response("Not found",status_code=404)
    return Response(storage.get(item["storage_key"]),media_type=item["content_type"],headers={"Content-Disposition":f'inline; filename="{item["name"]}"'})
@rt("/search")
def get(session,q:str=""):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    return views.list_page(identity,db.spaces(identity["org_id"]),db.pages(identity["org_id"]),"Search",db.search(identity["org_id"],q) if q else [])
@rt("/trash")
def get(session):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    deleted=[p for p in db.pages(identity["org_id"],True) if p["deleted_at"]]
    return views.list_page(identity,db.spaces(identity["org_id"]),db.pages(identity["org_id"]),"Trash",deleted)
@rt("/settings")
def get(session):
    identity=guard(session)
    if isinstance(identity,RedirectResponse):return identity
    return Html(views.head("Workspace settings · FastWiki"),Body(Div(H1("Workspace settings"),P("Create spaces and choose how your team can discuss pages."),Form(Input(name="name",placeholder="Space name",required=True),Input(name="description",placeholder="Description"),Select(Option("Organisation",value="org"),Option("Private",value="private"),name="visibility"),Select(Option("Page and inline",value="both"),Option("Page only",value="page"),Option("Inline only",value="inline"),Option("Off",value="off"),name="comments_mode"),Button("Create space",cls="btn"),method="post",action="/spaces",cls="smallform"),A("Back to wiki",href="/",cls="btn ghost"),cls="cardlist")))
@rt("/spaces")
def post(session,name:str,description:str="",visibility:str="org",comments_mode:str="both"):
    identity=guard(session)
    if not isinstance(identity,RedirectResponse):db.create_space(identity,name,description,visibility,comments_mode)
    return RedirectResponse("/",status_code=303)

register_seo_routes(app)
if __name__=="__main__":serve(port=int(os.getenv("FASTWIKI_PORT","5022")))
