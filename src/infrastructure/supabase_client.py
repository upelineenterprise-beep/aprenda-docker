import logging
from typing import Optional
import asyncpg
from src.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=2,
            max_size=10,
        )
    return _pool


async def checar_conexao() -> bool:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Erro ao checar conexão com banco: {e}")
        return False


async def buscar_empresa(phone: str) -> Optional[dict]:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM companies WHERE phone = $1 AND active = TRUE",
                phone,
            )
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Erro ao buscar empresa {phone}: {e}")
        return None


async def salvar_empresa(phone: str, dados: dict) -> Optional[dict]:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO companies (phone, name, monthly_costs, working_days, tax_pct, margin_pct, validity_days, email, instagram, active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE)
                ON CONFLICT (phone) DO UPDATE SET
                    name = EXCLUDED.name,
                    monthly_costs = EXCLUDED.monthly_costs,
                    working_days = EXCLUDED.working_days,
                    tax_pct = EXCLUDED.tax_pct,
                    margin_pct = EXCLUDED.margin_pct,
                    validity_days = EXCLUDED.validity_days,
                    email = EXCLUDED.email,
                    instagram = EXCLUDED.instagram,
                    updated_at = NOW()
                RETURNING *
                """,
                phone,
                dados["name"],
                dados["monthly_costs"],
                dados["working_days"],
                dados["tax_pct"],
                dados["margin_pct"],
                dados["validity_days"],
                dados.get("email"),
                dados.get("instagram"),
            )
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Erro ao salvar empresa {phone}: {e}")
        return None


async def salvar_orcamento(phone: str, dados: dict) -> Optional[str]:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO budgets (
                    company_phone, client_name, environments, project_days,
                    material_cost, displacement_cost, commission_pct, interest_pct,
                    payment_type, installments, final_price, daily_cost, pdf_url, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING id
                """,
                phone,
                dados["client_name"],
                dados["environments"],
                dados["project_days"],
                dados["material_cost"],
                dados.get("displacement_cost", 0),
                dados.get("commission_pct", 0),
                dados.get("interest_pct", 0),
                dados.get("payment_type", "avista"),
                dados.get("installments", 1),
                dados.get("final_price"),
                dados.get("daily_cost"),
                dados.get("pdf_url"),
                dados.get("status", "pending"),
            )
            return str(row["id"]) if row else None
    except Exception as e:
        logger.error(f"Erro ao salvar orçamento para {phone}: {e}")
        return None


async def atualizar_orcamento(budget_id: str, dados: dict) -> bool:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE budgets SET
                    final_price = COALESCE($2, final_price),
                    daily_cost = COALESCE($3, daily_cost),
                    pdf_url = COALESCE($4, pdf_url),
                    status = COALESCE($5, status)
                WHERE id = $1
                """,
                budget_id,
                dados.get("final_price"),
                dados.get("daily_cost"),
                dados.get("pdf_url"),
                dados.get("status"),
            )
            return True
    except Exception as e:
        logger.error(f"Erro ao atualizar orçamento {budget_id}: {e}")
        return False


async def listar_orcamentos(phone: str) -> list:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM budgets WHERE company_phone = $1 ORDER BY created_at DESC LIMIT 10",
                phone,
            )
            return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Erro ao listar orçamentos de {phone}: {e}")
        return []


async def salvar_mensagem(phone: str, direction: str, content: str, error_msg: str = None) -> None:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages (company_phone, direction, content, processed, error_msg)
                VALUES ($1, $2, $3, $4, $5)
                """,
                phone,
                direction,
                content,
                True,
                error_msg,
            )
    except Exception as e:
        logger.error(f"Erro ao salvar mensagem de {phone}: {e}")
