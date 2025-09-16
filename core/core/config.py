from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str | None = None
    MICROSERVICE_TOKEN: str
    MICROSERVICE_URL: str
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    @property
    def get_database_url(self):
        if self.SQLALCHEMY_DATABASE_URL:
            return self.SQLALCHEMY_DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
