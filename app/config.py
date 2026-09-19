from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    database_url: str = f"sqlite:///{ROOT / 'platform.db'}"
    workspace_root: Path = ROOT / 'workspace'
    secret_key: str = 'change-me-before-production'
    llm_provider: str = 'openrouter'
    openrouter_api_key: str | None = None
    openrouter_model: str = 'google/gemma-3-27b-it:free'
    max_iterations: int = 5
    git_remote: str = 'origin'
    enable_git_push: bool = False
settings = Settings()
settings.workspace_root.mkdir(parents=True, exist_ok=True)
