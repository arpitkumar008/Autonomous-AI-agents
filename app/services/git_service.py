from pathlib import Path
from ..tools.runtime import WorkspaceTools
from ..config import settings
class GitService:
    def checkpoint(self, workspace:Path, branch:str, description:str):
        t=WorkspaceTools(workspace)
        if not (workspace/'.git').exists(): t.run('git init')
        t.run('git config user.email forgeflow@local.invalid')
        t.run('git config user.name ForgeFlow')
        t.run('git checkout -B '+branch)
        t.run('git add .')
        result=t.run('git commit -m '+('checkpoint-'+description[:40].replace(' ','-')))
        head=t.run('git log -1 --format=%H')
        # Push is opt-in; the tool layer never permits a push to main.
        return (head.stdout.strip() if result.exit_code==0 else None), False, head.stdout
