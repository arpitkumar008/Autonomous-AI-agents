from pathlib import Path
import pytest
from app.tools.guardrails import Guardrails, GuardrailError
def test_workspace_confinement(tmp_path):
    g=Guardrails(tmp_path); assert g.path('frontend/app.py') == tmp_path/'frontend/app.py'
    with pytest.raises(GuardrailError): g.path('../../outside')
def test_secrets_and_commands_blocked(tmp_path):
    g=Guardrails(tmp_path)
    with pytest.raises(GuardrailError): g.path('.env')
    with pytest.raises(GuardrailError): g.command('git push origin main')
    with pytest.raises(GuardrailError): g.command('python main.py && whoami')
def test_safe_commands_allowed(tmp_path):
    g=Guardrails(tmp_path); g.command('python -m pytest -q'); g.command('npm run build')

