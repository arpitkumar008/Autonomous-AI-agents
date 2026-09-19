import re
from pathlib import Path
class GuardrailError(ValueError): pass
class Guardrails:
    SECRET_NAMES={'.env','.env.local','id_rsa','credentials.json'}
    ALLOWED=(r'^python( -m)? pytest( .*)?$',r'^pytest( .*)?$',r'^npm (test|run build|install)( .*)?$',r'^git (status|diff|add|commit|branch|checkout|init|remote|config|log)( .*)?$',r'^uvicorn [\w.:]+( .*)?$',r'^python [\w./-]+( .*)?$')
    def __init__(self, workspace: Path): self.workspace=workspace.resolve()
    def path(self, value: str|Path, write=False) -> Path:
        candidate=Path(value)
        resolved=(candidate if candidate.is_absolute() else self.workspace/candidate).resolve()
        if resolved != self.workspace and self.workspace not in resolved.parents: raise GuardrailError('Path escapes the project workspace')
        if any(part.lower() in self.SECRET_NAMES for part in resolved.parts): raise GuardrailError('Protected secret path')
        return resolved
    def command(self, command: str) -> None:
        normalized=' '.join(command.strip().split())
        if any(x in normalized for x in ('&&',';','|','>','<','`','$(', 'powershell','cmd.exe','rm ','del ','curl ','wget ')): raise GuardrailError('Shell composition or destructive/network command blocked')
        if re.search(r'git push\s+.*\bmain\b', normalized): raise GuardrailError('Push to main is always blocked')
        if not any(re.match(rule, normalized, re.I) for rule in self.ALLOWED): raise GuardrailError('Command is not in the allowlist')
