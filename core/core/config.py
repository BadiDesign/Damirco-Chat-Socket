from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str
    MICROSERVICE_TOKEN: str
    MICROSERVICE_URL: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
