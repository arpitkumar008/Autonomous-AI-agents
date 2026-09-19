import subprocess
from dataclasses import dataclass
from pathlib import Path
from .guardrails import Guardrails
@dataclass
class CommandResult: command:str; exit_code:int; stdout:str; stderr:str; timed_out:bool=False
class WorkspaceTools:
    def __init__(self, root: Path): self.root=root.resolve(); self.guard=Guardrails(self.root)
    def write(self,path:str,content:str):
        p=self.guard.path(path,write=True); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding='utf-8'); return str(p.relative_to(self.root))
    def read(self,path:str): return self.guard.path(path).read_text(encoding='utf-8')
    def list(self): return [str(p.relative_to(self.root)) for p in self.root.rglob('*') if p.is_file() and '.git' not in p.parts]
    def run(self, command:str, timeout:int=90):
        self.guard.command(command)
        try:
            p=subprocess.run(command.split(),cwd=self.root,capture_output=True,text=True,timeout=timeout,shell=False)
            return CommandResult(command,p.returncode,p.stdout[-12000:],p.stderr[-12000:])
        except subprocess.TimeoutExpired as e: return CommandResult(command,124,(e.stdout or '')[-12000:],(e.stderr or '')[-12000:],True)
