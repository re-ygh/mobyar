-- 01_schema.sql
-- ------------------------------------------------------------
-- Mobyar (موبیار) - Database Schema (PostgreSQL)
-- Phase 3 - Practical implementation
--
-- Notes:
-- - Naming is snake_case.
-- - We avoid reserved keyword "user" by using "users".
-- - Some columns were added to make Phase 3 practical (audit columns, statuses for sale, etc.).
-- ------------------------------------------------------------

-- Safety: allow rerun in dev environments
DROP TABLE IF EXISTS sale_item CASCADE;
DROP TABLE IF EXISTS sale CASCADE;
DROP TABLE IF EXISTS repair_order CASCADE;
DROP TABLE IF EXISTS inventory_history CASCADE;
DROP TABLE IF EXISTS product_price_history CASCADE;
DROP TABLE IF EXISTS service_price_history CASCADE;
DROP TABLE IF EXISTS customer_phone CASCADE;
DROP TABLE IF EXISTS phone_model CASCADE;
DROP TABLE IF EXISTS brand CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS service CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS role CASCADE;

-- ------------------------------------------------------------
-- 1) Base / lookup tables
-- ------------------------------------------------------------

CREATE TABLE role (
    role_id     SERIAL PRIMARY KEY,
    role_name   VARCHAR(20) NOT NULL UNIQUE,
    CONSTRAINT chk_role_name
        CHECK (role_name IN ('admin', 'staff', 'customer'))
);

CREATE TABLE users (
    user_id         BIGSERIAL PRIMARY KEY,
    name            VARCHAR(120) NOT NULL,
    phone           VARCHAR(20) NOT NULL UNIQUE,
    email           VARCHAR(255) UNIQUE,
    password_hash   TEXT NOT NULL,
    role_id         INT NOT NULL REFERENCES role(role_id) ON UPDATE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    signup_date     TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_user_status CHECK (status IN ('active', 'inactive')),
    CONSTRAINT chk_user_phone_format CHECK (phone ~ '^[0-9+]{10,20}$')
);

CREATE INDEX idx_users_role_id ON users(role_id);

-- ------------------------------------------------------------
-- 2) Phones (public data + customer-owned phones)
-- ------------------------------------------------------------

CREATE TABLE brand (
    brand_id    SERIAL PRIMARY KEY,
    brand_name  VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE phone_model (
    model_id    SERIAL PRIMARY KEY,
    model_name  VARCHAR(120) NOT NULL,
    brand_id    INT NOT NULL REFERENCES brand(brand_id) ON UPDATE CASCADE,
    CONSTRAINT uq_phone_model UNIQUE (brand_id, model_name)
);

CREATE INDEX idx_phone_model_brand_id ON phone_model(brand_id);

CREATE TABLE customer_phone (
    phone_id        BIGSERIAL PRIMARY KEY,
    model_id        INT NOT NULL REFERENCES phone_model(model_id) ON UPDATE CASCADE,
    color           VARCHAR(40),
    imei            VARCHAR(20) NOT NULL UNIQUE,
    customer_id     BIGINT NOT NULL REFERENCES users(user_id) ON UPDATE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_imei_format CHECK (imei ~ '^[0-9]{10,20}$')
);

CREATE INDEX idx_customer_phone_customer_id ON customer_phone(customer_id);
CREATE INDEX idx_customer_phone_model_id ON customer_phone(model_id);

-- ------------------------------------------------------------
-- 3) Products & services
-- ------------------------------------------------------------

CREATE TABLE category (
    category_id     SERIAL PRIMARY KEY,
    category_name   VARCHAR(120) NOT NULL UNIQUE,
    type            VARCHAR(20) NOT NULL DEFAULT 'public',

    CONSTRAINT chk_category_type CHECK (type IN ('public', 'private'))
);

CREATE TABLE product (
    product_id          BIGSERIAL PRIMARY KEY,
    name                VARCHAR(160) NOT NULL,
    description         TEXT,
    image               TEXT,
    current_price       NUMERIC(12,2) NOT NULL,
    stock               INT NOT NULL DEFAULT 0,
    category_id         INT NOT NULL REFERENCES category(category_id) ON UPDATE CASCADE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,

    -- For auditing triggers (who changed the price/stock)
    updated_by_user_id  BIGINT REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_product_price_nonneg CHECK (current_price >= 0),
    CONSTRAINT chk_product_stock_nonneg CHECK (stock >= 0)
);

-- Helpful indexes for typical store queries
CREATE INDEX idx_product_category_id ON product(category_id);
CREATE INDEX idx_product_stock ON product(stock);
CREATE INDEX idx_product_active ON product(is_active);

-- Optional: speed up search by name (case-insensitive)
CREATE INDEX idx_product_name_lower ON product((lower(name)));

CREATE TABLE service (
    service_id          BIGSERIAL PRIMARY KEY,
    service_name        VARCHAR(160) NOT NULL UNIQUE,
    description         TEXT,
    current_price       NUMERIC(12,2) NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,

    -- For auditing triggers (who changed the price)
    updated_by_user_id  BIGINT REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_service_price_nonneg CHECK (current_price >= 0)
);

CREATE INDEX idx_service_active ON service(is_active);

-- ------------------------------------------------------------
-- 4) Histories (price, inventory)
-- ------------------------------------------------------------

-- Phase 2 decision: split PriceHistory into two tables for true referential integrity.
CREATE TABLE product_price_history (
    price_id        BIGSERIAL PRIMARY KEY,
    product_id      BIGINT NOT NULL REFERENCES product(product_id) ON UPDATE CASCADE ON DELETE CASCADE,
    old_price       NUMERIC(12,2) NOT NULL,
    new_price       NUMERIC(12,2) NOT NULL,
    changed_by      BIGINT REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL,
    change_date     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_product_price_history_nonneg CHECK (old_price >= 0 AND new_price >= 0)
);

CREATE INDEX idx_pph_product_id_change_date ON product_price_history(product_id, change_date DESC);

CREATE TABLE service_price_history (
    price_id        BIGSERIAL PRIMARY KEY,
    service_id      BIGINT NOT NULL REFERENCES service(service_id) ON UPDATE CASCADE ON DELETE CASCADE,
    old_price       NUMERIC(12,2) NOT NULL,
    new_price       NUMERIC(12,2) NOT NULL,
    changed_by      BIGINT REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL,
    change_date     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_service_price_history_nonneg CHECK (old_price >= 0 AND new_price >= 0)
);

CREATE INDEX idx_sph_service_id_change_date ON service_price_history(service_id, change_date DESC);

-- Inventory history: we store old_stock/new_stock for audit + analytics.
CREATE TABLE inventory_history (
    inventory_id    BIGSERIAL PRIMARY KEY,
    product_id      BIGINT NOT NULL REFERENCES product(product_id) ON UPDATE CASCADE ON DELETE CASCADE,
    old_stock       INT NOT NULL,
    new_stock       INT NOT NULL,
    changed_by      BIGINT REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL,
    update_date     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_inventory_history_nonneg CHECK (old_stock >= 0 AND new_stock >= 0)
);

CREATE INDEX idx_inventory_product_id_update_date ON inventory_history(product_id, update_date DESC);

-- ------------------------------------------------------------
-- 5) Repairs
-- ------------------------------------------------------------

CREATE TABLE repair_order (
    repair_id            BIGSERIAL PRIMARY KEY,
    customer_id          BIGINT NOT NULL REFERENCES users(user_id) ON UPDATE CASCADE,
    phone_id             BIGINT NOT NULL REFERENCES customer_phone(phone_id) ON UPDATE CASCADE,
    service_id           BIGINT NOT NULL REFERENCES service(service_id) ON UPDATE CASCADE,
    price_at_time        NUMERIC(12,2) NOT NULL,
    status               VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_by_user_id   BIGINT REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE SET NULL,
    notes                TEXT,

    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_repair_price_nonneg CHECK (price_at_time >= 0),
    CONSTRAINT chk_repair_status CHECK (status IN ('pending', 'in_progress', 'ready', 'delivered', 'cancelled'))
);

CREATE INDEX idx_repair_customer_id ON repair_order(customer_id);
CREATE INDEX idx_repair_status ON repair_order(status);
CREATE INDEX idx_repair_created_at ON repair_order(created_at DESC);

-- ------------------------------------------------------------
-- 6) Sales
-- ------------------------------------------------------------

CREATE TABLE sale (
    sale_id             BIGSERIAL PRIMARY KEY,
    customer_id         BIGINT REFERENCES users(user_id) ON UPDATE CASCADE,
    created_by_user_id  BIGINT NOT NULL REFERENCES users(user_id) ON UPDATE CASCADE,
    sale_date           TIMESTAMPTZ NOT NULL DEFAULT now(),
    status              VARCHAR(12) NOT NULL DEFAULT 'draft',
    total_price         NUMERIC(12,2) NOT NULL DEFAULT 0,
    finalized_at        TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_sale_status CHECK (status IN ('draft', 'finalized', 'void')),
    CONSTRAINT chk_sale_total_nonneg CHECK (total_price >= 0)
);

CREATE INDEX idx_sale_sale_date ON sale(sale_date DESC);
CREATE INDEX idx_sale_status ON sale(status);

CREATE TABLE sale_item (
    sale_item_id    BIGSERIAL PRIMARY KEY,
    sale_id         BIGINT NOT NULL REFERENCES sale(sale_id) ON UPDATE CASCADE ON DELETE CASCADE,
    product_id      BIGINT NOT NULL REFERENCES product(product_id) ON UPDATE CASCADE,
    quantity        INT NOT NULL,
    price_at_time   NUMERIC(12,2) NOT NULL,

    CONSTRAINT chk_sale_item_qty_pos CHECK (quantity > 0),
    CONSTRAINT chk_sale_item_price_nonneg CHECK (price_at_time >= 0),
    CONSTRAINT uq_sale_item UNIQUE (sale_id, product_id)
);

CREATE INDEX idx_sale_item_sale_id ON sale_item(sale_id);
CREATE INDEX idx_sale_item_product_id ON sale_item(product_id);
