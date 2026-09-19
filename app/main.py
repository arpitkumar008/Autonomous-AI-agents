import asyncio, re
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from .config import settings
from .database import init_db, SessionLocal, User, Project, Event, TestRun, Checkpoint 
from .graph import execute_run
from .services.events import bus




app=FastAPI(title='ForgeFlow — Autonomous Development Platform')
app.add_middleware(SessionMiddleware,secret_key=settings.secret_key,https_only=False,same_site='lax')
app.mount('/static',StaticFiles(directory=Path(__file__).parent/'static'),name='static')
templates=Jinja2Templates(directory=Path(__file__).parent/'templates'); passwords=CryptContext(schemes=['pbkdf2_sha256'],deprecated='auto')
@app.on_event('startup')
def start(): init_db()
def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()
def current(request:Request, s=Depends(db)):
    uid=request.session.get('user_id'); user=s.get(User,uid) if uid else None
    if not user: raise HTTPException(401,'Sign in required')
    return user
def mine(project_id:int,user:User,s):
    p=s.get(Project,project_id)
    if not p or p.owner_id!=user.id: raise HTTPException(404,'Project not found')
    return p
def slugify(value): return re.sub('[^a-z0-9-]+','-',value.lower()).strip('-')[:60] or 'project'
@app.get('/',response_class=HTMLResponse)
def home(request:Request): return RedirectResponse('/dashboard' if request.session.get('user_id') else '/login')
@app.get('/login',response_class=HTMLResponse)
def login_page(request:Request): return templates.TemplateResponse(request,'login.html',{})
@app.post('/login')
def login(request:Request,username:str=Form(...),password:str=Form(...),s=Depends(db)):
    u=s.query(User).filter_by(username=username.strip().lower()).first()
    if not u or not passwords.verify(password,u.password_hash): return templates.TemplateResponse(request,'login.html',{'error':'Invalid credentials'},status_code=400)
    request.session['user_id']=u.id; return RedirectResponse('/dashboard',303)
@app.post('/register')
def register(request:Request,username:str=Form(...),password:str=Form(...),s=Depends(db)):
    username=slugify(username)
    if len(password)<8 or s.query(User).filter_by(username=username).first(): return templates.TemplateResponse(request,'login.html',{'error':'Username exists or password is under 8 characters'},status_code=400)
    u=User(username=username,password_hash=passwords.hash(password)); s.add(u);s.commit();request.session['user_id']=u.id;return RedirectResponse('/dashboard',303)
@app.post('/logout')
def logout(request:Request): request.session.clear();return RedirectResponse('/login',303)
@app.get('/dashboard',response_class=HTMLResponse)
def dashboard(request:Request,user=Depends(current),s=Depends(db)): return templates.TemplateResponse(request,'dashboard.html',{'user':user,'projects':s.query(Project).filter_by(owner_id=user.id).order_by(Project.id.desc()).all()})
@app.post('/projects')
def create_project(request:Request,name:str=Form(...),user=Depends(current),s=Depends(db)):
    base=slugify(name); slug=f'{base}-{user.id}'
    if s.query(Project).filter_by(slug=slug).first(): slug=f'{base}-{user.id}-{len(s.query(Project).all())}'
    path=settings.workspace_root/slug; path.mkdir(parents=True,exist_ok=False)
    p=Project(owner_id=user.id,name=name.strip(),slug=slug,workspace_path=str(path),branch=f'user/{user.username}');s.add(p);s.commit();return RedirectResponse(f'/projects/{p.id}',303)
@app.get('/projects/{project_id}',response_class=HTMLResponse)
def project_page(project_id:int,request:Request,user=Depends(current),s=Depends(db)):
    p=mine(project_id,user,s);return templates.TemplateResponse(request,'project.html',{'project':p,'events':s.query(Event).filter_by(project_id=p.id).order_by(Event.id.desc()).limit(100).all(),'tests':s.query(TestRun).filter_by(project_id=p.id).order_by(TestRun.id.desc()).limit(5).all(),'checkpoints':s.query(Checkpoint).filter_by(project_id=p.id).order_by(Checkpoint.id.desc()).all()})
@app.post('/projects/{project_id}/chat')
async def chat(project_id:int,request:Request,user=Depends(current),s=Depends(db)):
    p=mine(project_id,user,s); body=await request.json(); message=str(body.get('message','')).strip()
    if not message or len(message)>8000: raise HTTPException(422,'Requirement must be 1–8000 characters')
    asyncio.create_task(execute_run(p.id,message));return JSONResponse({'accepted':True,'status':'running'})
@app.get('/projects/{project_id}/api/state')
def state(project_id:int,user=Depends(current),s=Depends(db)):
    p=mine(project_id,user,s);return {'status':p.status,'demo_url':p.demo_url,'branch':p.branch,'workspace_path':p.workspace_path}
@app.websocket('/ws/projects/{project_id}')
async def websocket(project_id:int,ws:WebSocket):
    await ws.accept(); bus.clients[project_id].add(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: bus.clients[project_id].discard(ws)
