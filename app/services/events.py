import asyncio
from collections import defaultdict
from ..database import Event, SessionLocal
class EventBus:
    def __init__(self): self.clients=defaultdict(set)
    async def emit(self,project_id:int,agent:str,kind:str,message:str,run_id:int|None=None):
        db=SessionLocal(); db.add(Event(project_id=project_id,run_id=run_id,agent=agent,kind=kind,message=message)); db.commit(); db.close()
        payload='{"agent":"%s","kind":"%s","message":%s}'%(agent,kind,__import__('json').dumps(message))
        for ws in list(self.clients[project_id]):
            try: await ws.send_text(payload)
            except Exception: self.clients[project_id].discard(ws)
bus=EventBus()
