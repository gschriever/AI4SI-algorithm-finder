from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Algorithm Selector API"
    api_prefix: str = "/api"
    llm_provider: str = "openai_compatible"
    llm_api_key: str = ""
    llm_model: str = "gpt-5-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_chat_completions_path: str = "/chat/completions"
    llm_api_key_header: str = "Authorization"
    llm_api_key_prefix: str = "Bearer"
    llm_extra_headers_json: str = "{}"
    llm_timeout_seconds: float = 60.0
    research_mode: str = "fixture"
    research_academic_provider: str = "openalex"
    research_web_provider: str = "duckduckgo"
    research_academic_first: bool = True
    research_timeout_seconds: float = 20.0
    research_max_queries: int = 3
    research_max_results_per_query: int = 4
    research_max_sources: int = 8
    research_min_sources_before_web_fallback: int = 3
    research_openalex_base_url: str = "https://api.openalex.org"
    research_openalex_email: str = ""
    research_duckduckgo_base_url: str = "https://html.duckduckgo.com/html/"
    research_user_agent: str = "AlgorithmSelector/0.1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
