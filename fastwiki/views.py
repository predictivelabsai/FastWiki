from __future__ import annotations
import html, json
from fasthtml.common import *
from .seo import seo_meta
from urllib.parse import quote

ACCENT="#4f46e5"; TINT="#eef2ff"
FAVICON="data:image/svg+xml,"+quote('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="16" fill="#4f46e5"/><path fill="white" d="M13 17h9l5 27 5-18 5 18 5-27h9l-10 31h-9l-5-16-5 16h-9Z"/></svg>',safe="")
PARTNERS=(
    ("SAASPASS","https://saaspass.com/","https://saaspass.com/_next/static/assets/0176aeff921f6359fee88e796be31ace.png","Full-stack identity and access management spanning MFA, SSO, passwordless access and integration APIs."),
    ("Sixty Four","https://sixtyfour.ee/","https://sixtyfour.ee/favicon.ico","A senior Tallinn technology studio delivering software, AI consultancy, service design and public-sector programmes."),
    ("EDI Labs","https://edilabs.tech/","https://edilabs.tech/static/favicon.svg","AI and data engineering for document intelligence, forecasting, geospatial systems and agentic workflows."),
    ("Predictive Labs","https://predictivelabs.ai/","https://predictivelabs.ai/static/favicon.svg","Auditable AI systems for health, defence, public management, mobility and financial services."),
    ("Consistente","https://consistente.tech/","https://consistente.tech/static/favicon.svg","Enterprise AI delivery across financial services, healthcare, the public sector and technology."),
    ("Manmouna Technologies","https://manmouna.tech/","data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%230B1E14'/%3E%3Cpath d='M32 12 52 32 32 52 12 32Z' fill='%2334D399'/%3E%3Cpath d='M32 22 42 32 32 42 22 32Z' fill='%230B1E14'/%3E%3C/svg%3E","Auditable-by-design AI systems for European public services across health, defence, public management and mobility."),
)
BASE_CSS=r"""
:root{--accent:#4f46e5;--tint:#eef2ff;--ink:#172033;--muted:#667085;--line:#e5e7eb;--panel:#f8fafc}
*{box-sizing:border-box}body{margin:0;color:var(--ink);background:#fff;font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}a{color:inherit}
.nav{height:68px;display:flex;align-items:center;justify-content:space-between;max-width:1200px;margin:auto;padding:0 24px}.brand{display:flex;align-items:center;gap:10px;text-decoration:none;font-weight:800}.mark{width:34px;height:34px;background:var(--accent);color:#fff;border-radius:10px;display:grid;place-items:center}.navlinks{display:flex;gap:18px;align-items:center}.btn{display:inline-flex;align-items:center;justify-content:center;border:0;border-radius:10px;background:var(--accent);color:#fff;padding:11px 17px;font-weight:700;text-decoration:none;cursor:pointer}.btn.ghost{background:#fff;color:var(--ink);border:1px solid var(--line)}
.hero{max-width:1200px;margin:auto;padding:95px 24px 70px;display:grid;grid-template-columns:1.05fr .95fr;gap:68px;align-items:center}.eyebrow{color:var(--accent);font-weight:800;font-size:12px;letter-spacing:.17em;text-transform:uppercase}.hero h1{font-size:clamp(48px,6vw,76px);line-height:1.02;letter-spacing:-.055em;margin:18px 0}.hero p{font-size:20px;line-height:1.6;color:var(--muted)}.actions{display:flex;gap:12px;margin-top:28px}.mock{border:1px solid var(--line);border-radius:22px;padding:12px;background:#fff;box-shadow:0 30px 80px #312e8130}.mockin{height:430px;border-radius:14px;background:linear-gradient(135deg,#eef2ff,#fff);display:grid;grid-template-columns:150px 1fr}.mockside{padding:24px 15px;background:#f8fafc;border-radius:14px 0 0 14px}.mockline{height:10px;border-radius:99px;background:#dbe1ea;margin:14px 0}.mockpage{padding:48px 40px}.mockpage h3{font-size:30px;margin:0 0 24px}.mockpara{height:10px;background:#dbe1ea;border-radius:99px;margin:14px 0}.features{background:var(--panel);padding:82px 24px}.featuregrid{max-width:1200px;margin:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.feature{background:#fff;border:1px solid var(--line);border-radius:18px;padding:26px}.feature b{color:var(--accent)}.feature h2{font-size:20px}.feature p{color:var(--muted);line-height:1.6}.footer{max-width:1200px;margin:auto;padding:36px 24px;color:var(--muted);display:flex;justify-content:space-between}
.partners{max-width:1200px;margin:auto;padding:82px 24px;scroll-margin-top:80px}.partners h2{font-size:34px;margin:10px 0}.partners>p{max-width:720px;color:var(--muted);line-height:1.65}.partnergrid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:30px}.partner{min-width:0;border:1px solid var(--line);border-radius:17px;padding:18px;text-decoration:none}.partner img{width:44px;height:44px;object-fit:contain}.partner small{display:block;margin-top:14px;color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.08em}.partner h3{margin:7px 0}.partner p{font-size:12px;line-height:1.55;color:var(--muted)}
.shell{display:grid;grid-template-columns:260px minmax(0,1fr) 310px;height:100vh}.sidebar{background:#f8fafc;border-right:1px solid var(--line);padding:18px;overflow:auto}.sidehead{display:flex;align-items:center;justify-content:space-between;margin-bottom:22px}.user{font-size:12px;color:var(--muted);padding:11px 0;border-bottom:1px solid var(--line);margin-bottom:12px}.sideitem{display:block;text-decoration:none;padding:8px 10px;border-radius:8px;font-size:14px}.sideitem:hover,.sideitem.active{background:#e9eafc;color:var(--accent)}.treechild{padding-left:18px}.workspace{overflow:auto}.topbar{height:58px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px;padding:0 22px;position:sticky;top:0;background:#fffc;backdrop-filter:blur(10px);z-index:3}.search{border:1px solid var(--line);border-radius:9px;padding:9px 12px;min-width:260px}.editorwrap{max-width:880px;margin:auto;padding:54px 58px 120px}.titleinput{border:0;width:100%;font-size:42px;font-weight:800;letter-spacing:-.04em;outline:0;color:var(--ink)}.toolbar{display:flex;gap:4px;flex-wrap:wrap;margin:25px 0 16px;padding:7px;border:1px solid var(--line);border-radius:11px;position:sticky;top:68px;background:#fff;z-index:2}.tool{border:0;background:#fff;border-radius:6px;padding:7px 9px;cursor:pointer}.tool:hover{background:var(--tint)}.editor{min-height:430px;outline:0;font-size:17px;line-height:1.72}.editor h1,.editor h2,.editor h3{line-height:1.2}.editor img{max-width:100%}.editor table{border-collapse:collapse}.editor td,.editor th{border:1px solid var(--line);padding:7px}.ProseMirror:focus{outline:0}.status{font-size:12px;color:var(--muted);margin-left:auto}.rightbar{border-left:1px solid var(--line);padding:22px;overflow:auto;background:#fff}.panel{margin-bottom:28px}.panel h3{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}.comment{border:1px solid var(--line);border-radius:10px;padding:11px;margin:8px 0}.comment p{margin:5px 0;font-size:14px}.smallform{display:grid;gap:8px}.smallform input,.smallform textarea,.smallform select{width:100%;border:1px solid var(--line);border-radius:8px;padding:9px}.smallbtn{border:0;background:var(--accent);color:#fff;border-radius:8px;padding:8px 11px;font-weight:700;cursor:pointer}.cardlist{max-width:960px;margin:50px auto;padding:0 30px}.result{display:block;border-bottom:1px solid var(--line);padding:18px 4px;text-decoration:none}.result p{color:var(--muted)}.empty{padding:24px;color:var(--muted)}
@media(max-width:900px){.hero{grid-template-columns:1fr}.mock{display:none}.featuregrid,.partnergrid{grid-template-columns:1fr}.shell{grid-template-columns:210px 1fr}.rightbar{display:none}.editorwrap{padding:35px 26px}.titleinput{font-size:34px}}
"""

def head(title, public=False):
    return Head(Title(title),Meta(charset="utf-8"),Meta(name="viewport",content="width=device-width,initial-scale=1"),Meta(name="description",content="Open-source knowledge that works with your whole office suite."),*(seo_meta(title=title) if public else ()),Link(rel="icon",type="image/svg+xml",href=FAVICON),Link(rel="preconnect",href="https://fonts.googleapis.com"),Link(rel="stylesheet",href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"),Style(BASE_CSS))

def partner_section():
    return Section(Span("Partners",cls="eyebrow"),H2("Connect with trusted integration specialists."),P("Identity, software delivery, data engineering and applied-AI expertise for FastSME implementations."),Div(*[A(Img(src=logo,alt=f"{name} logo",loading="lazy"),Small("Integration Partner"),H3(name),P(description),href=url,target="_blank",rel="noopener noreferrer",cls="partner") for name,url,logo,description in PARTNERS],cls="partnergrid"),id="partners",cls="partners")

def landing(sign_in_href="/auth/suite"):
    return Html(head("FastWiki · Knowledge without lock-in", public=True),Body(
        Nav(A(Span("W",cls="mark"),"FastWiki",href="/",cls="brand"),Div(A("Partners",href="#partners"),A("Developers",href="/developers"),A("Sign In",href=sign_in_href,cls="btn ghost"),cls="navlinks"),cls="nav"),
        Main(Section(Div(Span("Open knowledge for independent teams",cls="eyebrow"),H1("Turn what your team knows into momentum."),P("A calm, connected workspace for handbooks, processes, project knowledge and decisions—open source, portable, and built for SMEs."),Div(A("Sign in to your workspace",href=sign_in_href,cls="btn"),A("Explore the API",href="/developers",cls="btn ghost"),cls="actions")),Div(Div(Div(Span("Spaces"),*[Div(cls="mockline") for _ in range(6)],cls="mockside"),Div(H3("Product launch playbook"),*[Div(cls="mockpara",style=f"width:{w}%") for w in (96,82,91,68,88,54)],cls="mockpage"),cls="mockin"),cls="mock"),cls="hero"),
        Section(Div(*[Article(B(f"0{i}"),H2(t),P(d),cls="feature") for i,(t,d) in enumerate([
            ("Write beautifully","Tiptap-powered rich editing with a portable JSON source and optional Markdown view."),
            ("Connect the work","Embed FastDocs, FastSheets, FastSlides, FastDrive and the rest of FastOffice."),
            ("Keep control","Organisation-scoped spaces, roles, recoverable trash and self-hosted or cloud storage."),
            ("Find the answer","Search titles and page content across every space in your organisation."),
            ("Discuss in context","Page and inline comments can be enabled independently for each space."),
            ("Build on it","Tenant-safe FastAPI endpoints, OpenAPI and Swagger schemas included.")
        ],1)],cls="featuregrid"),cls="features")),partner_section(),
        Footer(Span("FastWiki is part of the open-source FastOffice suite."),A("Discover freedom with open source →",href="https://office.fastsme.com"),cls="footer")))

def sidebar(who, spaces, pages, active=None):
    items=[]
    for space in spaces:
        children=[p for p in pages if p["space_id"]==space["id"] and not p["parent_id"]]
        items.extend([Div(B(space["name"]),cls="sideitem"),*[A("▱ "+p["title"],href=f"/pages/{p['id']}",cls="sideitem treechild"+(" active" if p["id"]==active else "")) for p in children]])
    return Aside(Div(A(Span("W",cls="mark"),"FastWiki",href="/",cls="brand"),A("＋",href="/pages/new",title="New page"),cls="sidehead"),Div(f"{who['name']} · {who['role']}",cls="user"),A("⌕ Search",href="/search",cls="sideitem"),*items,A("⚙ Workspace",href="/settings",cls="sideitem"),A("♻ Trash",href="/trash",cls="sideitem"),A("Sign out",href="/logout",cls="sideitem"),cls="sidebar")

EDITOR_JS=r"""
import { Editor } from 'https://esm.sh/@tiptap/core@3.6.6';
import StarterKit from 'https://esm.sh/@tiptap/starter-kit@3.6.6';
import Underline from 'https://esm.sh/@tiptap/extension-underline@3.6.6';
import Link from 'https://esm.sh/@tiptap/extension-link@3.6.6';
import Image from 'https://esm.sh/@tiptap/extension-image@3.6.6';
import { Table } from 'https://esm.sh/@tiptap/extension-table@3.6.6';
import { TableRow } from 'https://esm.sh/@tiptap/extension-table-row@3.6.6';
import { TableCell } from 'https://esm.sh/@tiptap/extension-table-cell@3.6.6';
import { TableHeader } from 'https://esm.sh/@tiptap/extension-table-header@3.6.6';
const el=document.querySelector('#editor');
const status=document.querySelector('#save-status');
const content=JSON.parse(document.querySelector('#initial-content').textContent);
const editor=new Editor({element:el,extensions:[StarterKit,Underline,Link.configure({openOnClick:false}),Image,Table.configure({resizable:true}),TableRow,TableCell,TableHeader],content,onUpdate:()=>queueSave()});
window.editor=editor;
document.querySelectorAll('[data-cmd]').forEach(b=>b.onclick=()=>{const c=editor.chain().focus(); const cmd=b.dataset.cmd;
 if(cmd==='bold')c.toggleBold().run(); if(cmd==='italic')c.toggleItalic().run(); if(cmd==='underline')c.toggleUnderline().run(); if(cmd==='h2')c.toggleHeading({level:2}).run(); if(cmd==='bullet')c.toggleBulletList().run(); if(cmd==='ordered')c.toggleOrderedList().run(); if(cmd==='quote')c.toggleBlockquote().run(); if(cmd==='code')c.toggleCodeBlock().run(); if(cmd==='table')c.insertTable({rows:3,cols:3,withHeaderRow:true}).run();});
let timer,version=Number(document.body.dataset.version);
const title=document.querySelector('#page-title'); title.addEventListener('input',queueSave);
function queueSave(){status.textContent='Unsaved changes';clearTimeout(timer);timer=setTimeout(save,700)}
async function save(){status.textContent='Saving…'; const res=await fetch(location.pathname+'/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:title.value,content_json:JSON.stringify(editor.getJSON()),markdown:document.querySelector('#markdown').value,version})}); const out=await res.json(); if(res.status===409){status.textContent='Newer version exists — reload';return} if(res.ok){version=out.version;document.body.dataset.version=version;status.textContent='Saved'}}
document.querySelector('#mode-rich').onclick=()=>{el.hidden=false;document.querySelector('#markdown').hidden=true};
document.querySelector('#mode-md').onclick=()=>{el.hidden=true;document.querySelector('#markdown').hidden=false};
document.querySelector('#markdown').addEventListener('input',queueSave);
"""

def page_shell(who,spaces,pages,current,comments,attachments,embeds):
    tools=[("B","bold"),("I","italic"),("U","underline"),("H2","h2"),("• List","bullet"),("1. List","ordered"),("❝","quote"),("</>","code"),("Table","table")]
    right=Aside(Div(H3("Comments"),*[Div(B(c["user_name"]),P(c["body"]),Small(c["kind"]),cls="comment") for c in comments],Form(Textarea(name="body",placeholder="Leave a comment",required=True),Select(Option("Page comment",value="page"),Option("Inline selection",value="inline"),name="kind"),Button("Comment",cls="smallbtn"),method="post",action=f"/pages/{current['id']}/comments",cls="smallform"),cls="panel"),Div(H3("Attachments"),*[A(a["name"],href=f"/attachments/{a['id']}",cls="result") for a in attachments],Form(Input(type="file",name="file",required=True),Button("Upload",cls="smallbtn"),method="post",action=f"/pages/{current['id']}/attachments",enctype="multipart/form-data",cls="smallform"),cls="panel"),Div(H3("FastOffice links"),*[A(f"{e['product']} · {e['title']}",href=e["url"],target="_blank",cls="result") for e in embeds],Form(Select(*[Option(p) for p in ("FastDocs","FastSheets","FastSlides","FastDrive","FastMeet","FastCal","FastMail","FastInsights","FastPilot")],name="product"),Input(name="title",placeholder="Resource title",required=True),Input(name="url",type="url",placeholder="https://…",required=True),Button("Add link",cls="smallbtn"),method="post",action=f"/pages/{current['id']}/embeds",cls="smallform"),cls="panel"),cls="rightbar")
    topbar=Div(
        Form(Input(name="q",placeholder="Search this workspace",cls="search"),method="get",action="/search"),
        A("New page",href="/pages/new",cls="btn ghost"),
        Span("Saved",id="save-status",cls="status"),cls="topbar")
    editor=Div(
        Input(value=current["title"],id="page-title",cls="titleinput",aria_label="Page title"),
        Div(*[Button(label,type="button",data_cmd=cmd,cls="tool") for label,cmd in tools],
            Button("Rich",id="mode-rich",type="button",cls="tool"),
            Button("Markdown",id="mode-md",type="button",cls="tool"),cls="toolbar"),
        Div(id="editor",cls="editor"),
        Textarea(current["markdown"],id="markdown",hidden=True,style="width:100%;min-height:430px"),
        Script(current["content_json"],type="application/json",id="initial-content"),
        Div(Form(Button("Move to trash",cls="btn ghost"),method="post",
                 action=f"/pages/{current['id']}/trash"),style="margin-top:50px"),
        cls="editorwrap")
    return Html(
        head(current["title"]+" · FastWiki"),
        Body(
            sidebar(who,spaces,pages,current["id"]),
            Main(topbar,editor,cls="workspace"),
            right,
            Script(EDITOR_JS,type="module"),
            cls="shell",data_version=str(current["version"])))

def list_page(who,spaces,pages,title,items,kind="search"):
    content=[A(H2(i["title"]),P((i.get("plain_text") or "")[:180]),href=f"/pages/{i['id']}",cls="result") for i in items]
    return Html(head(title+" · FastWiki"),Body(sidebar(who,spaces,pages),Main(Div(Form(Input(name="q",placeholder="Search pages",cls="search",autofocus=True),Button("Search",cls="btn"),method="get"),H1(title),*(content or [Div("Nothing here yet.",cls="empty")]),cls="cardlist"),cls="workspace"),cls="shell",style="grid-template-columns:260px 1fr"))
