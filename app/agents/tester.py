from pathlib import Path
from ..tools.runtime import WorkspaceTools
class TesterAgent:
    def test(self, workspace:Path):
        result=WorkspaceTools(workspace).run('python -m pytest -q',timeout=90)
        output=result.stdout+'\n'+result.stderr
        passed=0
        import re
        m=re.search(r'(\d+) passed',output); passed=int(m.group(1)) if m else 0
        return {'status':'PASS' if result.exit_code==0 else 'FAIL','total':passed if result.exit_code==0 else 0,'passed':passed,'output':output}
