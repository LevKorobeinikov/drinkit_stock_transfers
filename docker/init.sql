-- =========================
-- Таблица подразделений
-- =========================
CREATE TABLE IF NOT EXISTS units (
    id SERIAL PRIMARY KEY,
    unit_uuid UUID NOT NULL UNIQUE,
    unit_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =========================
-- Основная таблица перемещений
-- =========================
CREATE TABLE IF NOT EXISTS transfer_items (
    id BIGSERIAL PRIMARY KEY,
    transfer_order_id VARCHAR(50) NOT NULL,
    transfer_order_number VARCHAR(50),

    origin_unit_id UUID NOT NULL REFERENCES units(unit_uuid),
    destination_unit_id UUID NOT NULL REFERENCES units(unit_uuid),

    stock_item_id UUID NOT NULL,
    stock_item_name TEXT,

    ordered_quantity DECIMAL(10,3),
    shipped_quantity DECIMAL(10,3),
    received_quantity DECIMAL(10,3),

    measurement_unit VARCHAR(50),
    price_per_unit_with_vat DECIMAL(10,2),
    sum_price_with_vat DECIMAL(10,2),

    expected_at_local TIMESTAMP,
    shipped_at_local TIMESTAMP,
    received_at_local TIMESTAMP,

    status VARCHAR(50),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT transfer_items_unique UNIQUE (transfer_order_id, stock_item_id)
);

-- =========================
-- Индексы
-- =========================
CREATE INDEX IF NOT EXISTS idx_transfer_items_origin
    ON transfer_items(origin_unit_id);

CREATE INDEX IF NOT EXISTS idx_transfer_items_destination
    ON transfer_items(destination_unit_id);

CREATE INDEX IF NOT EXISTS idx_transfer_items_received
    ON transfer_items(received_at_local);

CREATE INDEX IF NOT EXISTS idx_transfer_items_status
    ON transfer_items(status);

CREATE INDEX IF NOT EXISTS idx_transfer_items_shipped
    ON transfer_items(shipped_quantity);

-- =========================
-- Наполнение units
-- =========================
INSERT INTO units (unit_uuid, unit_name) VALUES
('11f030c2a0d76780b43603989d600630', 'Пермь 1-1'),
('11f06df2a2dfc3d41ec03e0cecf381a0', 'Пермь 1-2'),
('11f06df48cb8c5197dc202d329827a30', 'Пермь 1-3'),
('11f0939995c39bd0a5eabe3ce1e906f0', 'Пермь 1-5'),
('1650a826-d2b6-92e2-11ef-8565c1d53f28', 'Пермь-ПРЦ-1')
ON CONFLICT (unit_uuid) DO NOTHING;

-- =========================
-- Права
-- =========================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO myuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO myuser;
GRANT ALL ON SCHEMA public TO myuser;

ALTER TABLE transfer_items OWNER TO myuser;
ALTER TABLE units OWNER TO myuser;