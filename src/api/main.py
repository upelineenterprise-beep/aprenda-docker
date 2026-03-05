import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.webhook import router as webhook_router
from src.infrastructure.supabase_client import checar_conexao

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_ok = await checar_conexao()
    if db_ok:
        logger.info("Conexão com banco de dados OK.")
    else:
        logger.warning("Não foi possível conectar ao banco de dados na inicialização.")
    yield
    logger.info("Servidor encerrando.")


app = FastAPI(
    title="Zé Calculei",
    description="Assistente WhatsApp para orçamentos de marceneiros",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(webhook_router)


@app.get("/health")
async def health():
    db_ok = await checar_conexao()
    return {"status": "ok", "database": "ok" if db_ok else "error"}
