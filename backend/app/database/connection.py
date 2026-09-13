from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from sqlcipher3 import dbapi2 as sqlite3

from app.security.key_manager import get_or_create_database_key
from app.utils.logger import logger


DB_DIR = Path("data")
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "networkmap.db"

Base = declarative_base()


def get_db_connection():
    """
    Cria uma NOVA conexão SQLCipher completamente inicializada.

    Como usamos NullPool, cada checkout do SQLAlchemy recebe uma
    conexão nova e ela é fechada após o uso.
    """

    connection = sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False,
        timeout=30,
    )

    try:
        db_key = get_or_create_database_key()
        safe_key = db_key.replace("'", "''")

        cursor = connection.cursor()

        try:
            # A chave precisa ser aplicada antes de qualquer operação no banco.
            cursor.execute(f"PRAGMA key = '{safe_key}'")

            # Força uma leitura para validar imediatamente a chave.
            cursor.execute("SELECT count(*) FROM sqlite_master")
            cursor.fetchone()

            cursor.execute("PRAGMA foreign_keys = ON")

            # Aguarda alguns segundos em caso de banco ocupado,
            # ao invés de falhar imediatamente.
            cursor.execute("PRAGMA busy_timeout = 5000")

            # Mantém WAL, pois o banco já está utilizando essa configuração.
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.fetchone()

        finally:
            cursor.close()

        return connection

    except Exception:
        connection.close()
        raise


engine = create_engine(
    "sqlite://",
    creator=get_db_connection,

    # IMPORTANTE:
    # não reutilizar conexões SQLCipher entre requests.
    poolclass=NullPool,

    # Mostra que a conexão deve ser tratada pelo SQLAlchemy normalmente.
    future=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def init_db():
    try:
        Base.metadata.create_all(bind=engine)

        logger.info(
            "Database schema verified and initialized successfully."
        )

    except Exception as e:
        logger.error(
            f"Error initializing database schema: {e}"
        )
        raise








