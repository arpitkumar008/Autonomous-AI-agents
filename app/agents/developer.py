from pathlib import Path
from ..tools.runtime import WorkspaceTools

APP='''<!doctype html><html><head><meta charset="utf-8"><title>{{ title }}</title><style>body{font-family:system-ui;max-width:900px;margin:auto;padding:2rem;background:#0f172a;color:#e2e8f0}nav{display:flex;gap:1rem;justify-content:space-between}a,button{color:#67e8f9}main{background:#172554;padding:2rem;border-radius:1rem}.card{background:#1e293b;padding:1rem;margin:1rem 0;border-radius:.5rem}input,button{padding:.65rem;margin:.25rem}button{background:#0891b2;border:0;border-radius:.35rem;color:#fff}</style></head><body><nav><b>{{ title }}</b><span>Home · Products · Cart · Account</span></nav><main><h1>{{ title }}</h1><p>{{ description }}</p><section id="products"><h2>Products</h2>{% for p in products %}<div class="card"><b>{{ p.name }}</b><p>${{ p.price }}</p><button onclick="add({{ p.id }})">Add to cart</button></div>{% endfor %}</section><section class="card"><h2>Cart <span id="count">0</span></h2><button onclick="checkout()">Checkout</button><p id="notice"></p></section><section class="card"><h2>Login</h2><input id="email" placeholder="Email"><button onclick="login()">Login</button></section></main><script>let count=0;async function add(id){let r=await fetch('/api/cart',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({product_id:id})});let d=await r.json();count=d.count;document.querySelector('#count').textContent=count}async function login(){let r=await fetch('/api/login',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({email:email.value})});notice.textContent=(await r.json()).message}async function checkout(){let r=await fetch('/api/checkout',{method:'POST'});notice.textContent=(await r.json()).message}</script></body></html>'''
MAIN='''from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path
from jinja2 import Template
app=FastAPI(title="Generated App")
PRODUCTS=[{"id":1,"name":"Starter product","price":29},{"id":2,"name":"Premium product","price":79}]
cart=[]
class CartItem(BaseModel): product_id:int
class Login(BaseModel): email:str
@app.get('/',response_class=HTMLResponse)
def home(): return Template(Path('frontend/index.html').read_text()).render(title="{{TITLE}}",description="{{DESCRIPTION}}",products=PRODUCTS)
@app.get('/api/products')
def products(): return PRODUCTS
@app.get('/api/products/{product_id}')
def product(product_id:int):
    item=next((p for p in PRODUCTS if p['id']==product_id),None)
    if not item: raise HTTPException(404,'Product not found')
    return item
@app.post('/api/cart')
def add_cart(item:CartItem):
    if not any(p['id']==item.product_id for p in PRODUCTS): raise HTTPException(404,'Product not found')
    cart.append(item.product_id); return {'count':len(cart)}
@app.post('/api/login')
def login(data:Login):
    if '@' not in data.email: raise HTTPException(422,'Valid email required')
    return {'message':'Logged in'}
@app.post('/api/checkout')
def checkout():
    if not cart: raise HTTPException(400,'Cart is empty')
    cart.clear(); return {'message':'Order created'}
'''
TEST='''from fastapi.testclient import TestClient
from backend.main import app
c=TestClient(app)
def test_home(): assert c.get('/').status_code==200
def test_catalog_and_detail(): assert c.get('/api/products').status_code==200; assert c.get('/api/products/1').status_code==200; assert c.get('/api/products/999').status_code==404
def test_cart_and_checkout(): assert c.post('/api/cart',json={'product_id':1}).json()['count']>=1; assert c.post('/api/checkout').status_code==200
def test_login_validation(): assert c.post('/api/login',json={'email':'a@b.com'}).status_code==200; assert c.post('/api/login',json={'email':'bad'}).status_code==422
'''
class DeveloperAgent:
    def implement(self, workspace:Path, request:str, incremental:bool)->list[str]:
        tools=WorkspaceTools(workspace); text=request.lower(); title='Wishlist Store' if 'wishlist' in text else 'Autonomous Commerce Demo' if 'commerce' in text or 'e-commerce' in text else 'Generated Web Application'
        description='A local-first generated web application, validated by executable API tests.'
        changed=[]
        if not (workspace/'backend/main.py').exists():
            changed += [tools.write('frontend/index.html',APP), tools.write('backend/main.py',MAIN.replace('{{TITLE}}',title).replace('{{DESCRIPTION}}',description)),tools.write('tests/test_app.py',TEST),tools.write('requirements.txt','fastapi\nuvicorn\njinja2\npytest\nhttpx\n'),tools.write('README.md',f'# {title}\n\nGenerated from: {request}\n\nRun: `uvicorn backend.main:app --port 8001`\n')]
        elif 'wishlist' in text:
            source=tools.read('backend/main.py')
            if '/api/wishlist' not in source:
                source=source.replace("cart=[]", "cart=[]\nwishlist=[]")+"\n@app.post('/api/wishlist/{product_id}')\ndef add_wishlist(product_id:int):\n    if not any(p['id']==product_id for p in PRODUCTS): raise HTTPException(404,'Product not found')\n    if product_id not in wishlist: wishlist.append(product_id)\n    return {'count':len(wishlist)}\n"
                changed.append(tools.write('backend/main.py',source))
                test=tools.read('tests/test_app.py')+"\ndef test_wishlist(): assert c.post('/api/wishlist/1').status_code==200; assert c.post('/api/wishlist/999').status_code==404\n"
                changed.append(tools.write('tests/test_app.py',test))
        return changed
