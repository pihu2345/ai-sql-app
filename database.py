import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ─── MySQL Connection ──────────────────────────────────────────────────────────

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME     = os.getenv("DB_NAME", "ai_app_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Connection alive check
    pool_recycle=3600,        # 1 hour mein connection recycle
    echo=False                # True karo agar SQL debug karna ho
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Dependency Injection ──────────────────────────────────────────────────────

def get_db():
    """FastAPI dependency — DB session provide karta hai, automatically close karta hai"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── SQL Service ───────────────────────────────────────────────────────────────

class SQLService:
    """
    Raw SQL operations ke liye service.
    Schema introspection aur query execution handle karta hai.
    """

    def test_connection(self) -> bool:
        """Database connection test karo"""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def execute_query(self, query: str) -> list:
        """
        SELECT query execute karo aur results list of dicts mein return karo.
        """
        with engine.connect() as conn:
            result = conn.execute(text(query))
            columns = list(result.keys())
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    def get_all_tables(self) -> list:
        """Database mein saari tables ki list"""
        inspector = inspect(engine)
        return inspector.get_table_names()

    def get_schema_info(self) -> str:
        """
        Poore database ka schema text format mein return karo.
        Groq ko context dene ke liye use hota hai.
        """
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        schema_lines = []
        for table in tables:
            cols = inspector.get_columns(table)
            col_defs = ", ".join(
                f"{c['name']} ({str(c['type'])})" for c in cols
            )
            schema_lines.append(f"Table `{table}`: {col_defs}")

        return "\n".join(schema_lines) if schema_lines else "Database mein koi table nahi mili."

    def get_table_preview(self, table_name: str, limit: int = 5) -> list:
        """Kisi table ke pehle N rows dekhho"""
        return self.execute_query(f"SELECT * FROM `{table_name}` LIMIT {limit}")
