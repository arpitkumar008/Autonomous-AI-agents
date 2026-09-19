import httpx
from ..config import settings
class LLMGateway:
    async def generate(self, system: str, prompt: str) -> str:
        if not settings.openrouter_api_key: return ''
        headers={'Authorization':f'Bearer {settings.openrouter_api_key}','HTTP-Referer':'http://localhost:8000','X-Title':'Autonomous Dev Platform'}
        payload={'model':settings.openrouter_model,'messages':[{'role':'system','content':system},{'role':'user','content':prompt}], 'temperature':0.2}
        async with httpx.AsyncClient(timeout=45) as c:
            r=await c.post('https://openrouter.ai/api/v1/chat/completions',headers=headers,json=payload); r.raise_for_status(); return r.json()['choices'][0]['message']['content']
gateway=LLMGateway()
