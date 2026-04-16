from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/llm_ufc"

    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Gemini (Google) — se preenchido, tem prioridade sobre OpenAI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Groq — se preenchido, tem prioridade sobre OpenAI (mas não sobre Gemini)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Server
    APP_NAME: str = "PoC LLM UFC"
    DEBUG: bool = False

    # Testes de carga — desabilita validação de JWT quando True
    LOAD_TEST_MODE: bool = True
    LOAD_TEST_PROFESSOR_ID: int = 1

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
