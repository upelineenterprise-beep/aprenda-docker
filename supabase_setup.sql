-- ============================================================
-- Zé Calculei — Setup do Banco Supabase
-- ============================================================

-- Extensão para UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- Tabela: companies
-- Dados de cada marceneiro/empresa cadastrada via onboarding
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone        VARCHAR(20) UNIQUE NOT NULL,
    name         VARCHAR(100) NOT NULL,
    monthly_costs NUMERIC(12, 2) NOT NULL,
    working_days  INTEGER NOT NULL,
    tax_pct       NUMERIC(5, 2) NOT NULL DEFAULT 0,
    margin_pct    NUMERIC(5, 2) NOT NULL DEFAULT 0,
    validity_days INTEGER NOT NULL DEFAULT 10,
    email         VARCHAR(200),
    instagram     VARCHAR(100),
    active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companies_phone ON companies(phone);

-- ============================================================
-- Tabela: budgets
-- Cada orçamento gerado
-- ============================================================
CREATE TABLE IF NOT EXISTS budgets (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_phone     VARCHAR(20) NOT NULL,
    client_name       VARCHAR(100) NOT NULL,
    environments      TEXT NOT NULL,
    project_days      INTEGER NOT NULL,
    material_cost     NUMERIC(12, 2) NOT NULL DEFAULT 0,
    displacement_cost NUMERIC(12, 2) NOT NULL DEFAULT 0,
    commission_pct    NUMERIC(5, 2) NOT NULL DEFAULT 0,
    interest_pct      NUMERIC(5, 2) NOT NULL DEFAULT 0,
    payment_type      VARCHAR(20) NOT NULL DEFAULT 'avista',
    installments      INTEGER NOT NULL DEFAULT 1,
    final_price       NUMERIC(12, 2),
    daily_cost        NUMERIC(12, 2),
    pdf_url           TEXT,
    status            VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_budgets_company_phone ON budgets(company_phone);
CREATE INDEX IF NOT EXISTS idx_budgets_created_at ON budgets(created_at DESC);

-- ============================================================
-- Tabela: messages
-- Histórico de todas as mensagens trocadas
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_phone VARCHAR(20) NOT NULL,
    direction     VARCHAR(3) NOT NULL CHECK (direction IN ('IN', 'OUT')),
    content       TEXT NOT NULL,
    processed     BOOLEAN NOT NULL DEFAULT TRUE,
    error_msg     TEXT,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_company_phone ON messages(company_phone);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

-- ============================================================
-- RLS desabilitado por enquanto
-- ============================================================
ALTER TABLE companies DISABLE ROW LEVEL SECURITY;
ALTER TABLE budgets DISABLE ROW LEVEL SECURITY;
ALTER TABLE messages DISABLE ROW LEVEL SECURITY;

-- ============================================================
-- Dados fictícios para teste
-- ============================================================

INSERT INTO companies (phone, name, monthly_costs, working_days, tax_pct, margin_pct, validity_days, email)
VALUES
    ('5511999990001', 'Marcenaria Silva', 10000.00, 22, 6.00, 30.00, 10, 'silva@marcenaria.com'),
    ('5511999990002', 'Móveis Souza',     15000.00, 20, 8.00, 35.00, 15, 'souza@moveis.com')
ON CONFLICT (phone) DO NOTHING;

INSERT INTO budgets (
    company_phone, client_name, environments, project_days,
    material_cost, displacement_cost, commission_pct, interest_pct,
    payment_type, installments, final_price, daily_cost, status
) VALUES (
    '5511999990001', 'João da Silva', 'Suite casal e closet', 5,
    5000.00, 0.00, 10.00, 1.00,
    'parcelado', 3, 13722.07, 454.55, 'done'
);
