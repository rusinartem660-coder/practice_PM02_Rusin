-- ============================================================
-- База данных для криптобиржи CoinGuard
-- Вариант 6: Криптобиржа с оборотом $10 млрд в день
-- ВЕРСИЯ ДЛЯ MYSQL - ТОЛЬКО SQL
-- ============================================================

-- Удаление базы данных, если существует
DROP DATABASE IF EXISTS coinguard;

-- Создание базы данных
CREATE DATABASE coinguard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Использование базы данных
USE coinguard;

-- ============================================================
-- 1. БЛОКЧЕЙН-УЗЛЫ
-- ============================================================

-- Блокчейн-узлы
CREATE TABLE blockchain_nodes (
    node_id INT AUTO_INCREMENT PRIMARY KEY,
    blockchain_name VARCHAR(50) NOT NULL,
    node_type VARCHAR(20) NOT NULL,
    endpoint VARCHAR(255),
    network VARCHAR(20) DEFAULT 'mainnet',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Блоки блокчейна
CREATE TABLE blockchain_blocks (
    block_id INT AUTO_INCREMENT PRIMARY KEY,
    node_id INT,
    block_height BIGINT NOT NULL,
    block_hash VARCHAR(100) NOT NULL,
    parent_hash VARCHAR(100),
    block_timestamp TIMESTAMP NOT NULL,
    transaction_count INT DEFAULT 0,
    size_bytes BIGINT,
    is_fork TINYINT(1) DEFAULT 0,
    is_reorg TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES blockchain_nodes(node_id),
    UNIQUE KEY uk_node_height (node_id, block_height),
    UNIQUE KEY uk_node_hash (node_id, block_hash)
);

-- Транзакции блокчейна
CREATE TABLE blockchain_transactions (
    tx_id INT AUTO_INCREMENT PRIMARY KEY,
    block_id INT,
    tx_hash VARCHAR(100) NOT NULL,
    from_address VARCHAR(100),
    to_address VARCHAR(100),
    amount DECIMAL(38, 18),
    fee DECIMAL(38, 18),
    tx_type VARCHAR(30),
    status VARCHAR(20) DEFAULT 'confirmed',
    confirmation_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (block_id) REFERENCES blockchain_blocks(block_id),
    UNIQUE KEY uk_tx_hash (tx_hash)
);

-- Индексы для blockchain
CREATE INDEX idx_blocks_height ON blockchain_blocks(block_height);
CREATE INDEX idx_blocks_timestamp ON blockchain_blocks(block_timestamp);
CREATE INDEX idx_transactions_hash ON blockchain_transactions(tx_hash);

-- ============================================================
-- 2. ТОРГОВЛЯ
-- ============================================================

-- Торговые пары
CREATE TABLE trading_pairs (
    pair_id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    base_asset VARCHAR(10) NOT NULL,
    quote_asset VARCHAR(10) NOT NULL,
    min_order_size DECIMAL(38, 18),
    max_order_size DECIMAL(38, 18),
    tick_size DECIMAL(38, 18),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ордера
CREATE TABLE trading_orders (
    order_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    pair_id INT,
    user_id INT NOT NULL,
    order_type VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,
    price DECIMAL(38, 18),
    quantity DECIMAL(38, 18) NOT NULL,
    filled_quantity DECIMAL(38, 18) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (pair_id) REFERENCES trading_pairs(pair_id)
);

-- История сделок
CREATE TABLE trade_history (
    trade_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    pair_id INT,
    buy_order_id BIGINT,
    sell_order_id BIGINT,
    price DECIMAL(38, 18) NOT NULL,
    quantity DECIMAL(38, 18) NOT NULL,
    total DECIMAL(38, 18) NOT NULL,
    buyer_id INT NOT NULL,
    seller_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pair_id) REFERENCES trading_pairs(pair_id),
    FOREIGN KEY (buy_order_id) REFERENCES trading_orders(order_id),
    FOREIGN KEY (sell_order_id) REFERENCES trading_orders(order_id)
);

-- Индексы для торговли
CREATE INDEX idx_orders_user ON trading_orders(user_id, status);
CREATE INDEX idx_orders_pair ON trading_orders(pair_id, status);
CREATE INDEX idx_trade_history_time ON trade_history(created_at);

-- ============================================================
-- 3. ПОЛЬЗОВАТЕЛИ
-- ============================================================

-- Пользователи
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    kyc_status VARCHAR(20) DEFAULT 'pending',
    kyc_level INT DEFAULT 1,
    daily_limit DECIMAL(38, 18),
    monthly_limit DECIMAL(38, 18),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Балансы пользователей
CREATE TABLE user_balances (
    balance_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    asset VARCHAR(10) NOT NULL,
    available DECIMAL(38, 18) DEFAULT 0,
    locked DECIMAL(38, 18) DEFAULT 0,
    total DECIMAL(38, 18) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE KEY uk_user_asset (user_id, asset)
);

-- HSM ключи
CREATE TABLE hsm_keys (
    key_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    key_type VARCHAR(20) NOT NULL,
    key_identifier VARCHAR(100) NOT NULL,
    encrypted_key TEXT NOT NULL,
    key_share_1 TEXT,
    key_share_2 TEXT,
    key_share_3 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- История транзакций
CREATE TABLE user_transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    tx_type VARCHAR(30) NOT NULL,
    asset VARCHAR(10) NOT NULL,
    amount DECIMAL(38, 18) NOT NULL,
    fee DECIMAL(38, 18) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    reference_id VARCHAR(100),
    blockchain_tx_hash VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Индексы для пользователей
CREATE INDEX idx_balances_user ON user_balances(user_id);
CREATE INDEX idx_user_transactions_user ON user_transactions(user_id, created_at);

-- ============================================================
-- 4. АУДИТ
-- ============================================================

-- Логи аудита
CREATE TABLE audit_log (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_id INT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    event_data JSON,
    source_system VARCHAR(50),
    transaction_hash VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AML проверки
CREATE TABLE aml_checks (
    check_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    check_type VARCHAR(50) NOT NULL,
    risk_score DECIMAL(5, 2),
    status VARCHAR(20) DEFAULT 'passed',
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Индексы для аудита
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_time ON audit_log(created_at);

-- ============================================================
-- 5. МЕТАДАННЫЕ БЭКАПОВ
-- ============================================================

CREATE TABLE backup_history (
    backup_id INT AUTO_INCREMENT PRIMARY KEY,
    backup_type VARCHAR(20) NOT NULL,
    backup_name VARCHAR(100) NOT NULL,
    component VARCHAR(50) NOT NULL,
    size_bytes BIGINT,
    checksum_sha256 VARCHAR(64),
    backup_location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'completed',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retention_until TIMESTAMP,
    encryption_used TINYINT(1) DEFAULT 0
);

CREATE INDEX idx_backup_component ON backup_history(component);
CREATE INDEX idx_backup_status ON backup_history(status);

-- ============================================================
-- 6. ТЕСТОВЫЕ ДАННЫЕ
-- ============================================================

-- Торговые пары
INSERT INTO trading_pairs (symbol, base_asset, quote_asset, min_order_size, max_order_size, tick_size) VALUES
('BTC/USDT', 'BTC', 'USDT', 0.0001, 100, 0.01),
('ETH/USDT', 'ETH', 'USDT', 0.001, 1000, 0.01),
('SOL/USDT', 'SOL', 'USDT', 0.01, 10000, 0.001),
('DOGE/USDT', 'DOGE', 'USDT', 1, 1000000, 0.0001);

-- Пользователи
INSERT INTO users (username, email, kyc_status, kyc_level) VALUES
('trader1', 'trader1@example.com', 'verified', 3),
('trader2', 'trader2@example.com', 'verified', 2),
('whale1', 'whale1@example.com', 'verified', 5),
('institutional1', 'inst1@example.com', 'verified', 5),
('retail1', 'retail1@example.com', 'verified', 1);

-- Балансы
INSERT INTO user_balances (user_id, asset, available, locked) VALUES
(1, 'BTC', 1.5, 0.2),
(1, 'USDT', 100000, 5000),
(2, 'ETH', 50, 5),
(2, 'USDT', 50000, 0),
(3, 'BTC', 500, 100),
(3, 'USDT', 5000000, 100000),
(3, 'ETH', 10000, 1000),
(4, 'BTC', 1000, 200),
(4, 'USDT', 10000000, 500000);

-- Блокчейн-узлы
INSERT INTO blockchain_nodes (blockchain_name, node_type, endpoint) VALUES
('Bitcoin', 'archive', 'https://bitcoin-node.local:8332'),
('Ethereum', 'archive', 'https://ethereum-node.local:8545'),
('Solana', 'full', 'https://solana-node.local:8899');

-- Блоки
INSERT INTO blockchain_blocks (node_id, block_height, block_hash, parent_hash, block_timestamp, transaction_count) VALUES
(1, 800000, '0000000000000000000123456789abcdef', '0000000000000000000fedcba987654', NOW() - INTERVAL 1 HOUR, 2500),
(1, 800001, '0000000000000000000123456789abcde0', '0000000000000000000123456789abcdef', NOW() - INTERVAL 30 MINUTE, 2800),
(2, 18000000, '0x123456789abcdef123456789abcdef123456789a', '0xabcdef123456789abcdef123456789abcdef12345', NOW() - INTERVAL 1 HOUR, 150),
(2, 18000001, '0x123456789abcdef123456789abcdef123456789b', '0x123456789abcdef123456789abcdef123456789a', NOW() - INTERVAL 30 MINUTE, 180);

-- Ордера
INSERT INTO trading_orders (pair_id, user_id, order_type, side, price, quantity, filled_quantity, status) VALUES
(1, 1, 'LIMIT', 'BUY', 65000, 0.5, 0.5, 'filled'),
(1, 2, 'LIMIT', 'SELL', 68000, 0.3, 0, 'open'),
(2, 3, 'LIMIT', 'BUY', 3500, 10, 5, 'partial'),
(1, 4, 'MARKET', 'BUY', NULL, 2, 2, 'filled');

-- Сделки
INSERT INTO trade_history (pair_id, buy_order_id, sell_order_id, price, quantity, total, buyer_id, seller_id) VALUES
(1, 1, 2, 66000, 0.5, 33000, 1, 2),
(1, 4, 2, 67000, 2, 134000, 4, 2);

-- История бэкапов
INSERT INTO backup_history (backup_type, backup_name, component, size_bytes, checksum_sha256, backup_location, status, started_at, completed_at, encryption_used) VALUES
('full', 'coinguard_full_20260616_0200', 'mysql', 5368709120, 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6', 's3://coinguard-backups/full/', 'completed', '2026-06-16 02:00:00', '2026-06-16 03:00:00', 1);

-- AML проверки
INSERT INTO aml_checks (user_id, check_type, risk_score, status, details) VALUES
(1, 'initial_screening', 15.5, 'passed', '{"reason": "low_risk"}'),
(3, 'initial_screening', 45.0, 'review', '{"reason": "high_volume"}'),
(4, 'periodic_review', 20.0, 'passed', '{"reason": "institutional"}');

-- ============================================================
-- 7. ПРЕДСТАВЛЕНИЯ ДЛЯ МОНИТОРИНГА
-- ============================================================

CREATE VIEW view_current_balances AS
SELECT 
    u.username,
    b.asset,
    b.available,
    b.locked,
    b.total,
    b.updated_at
FROM users u
JOIN user_balances b ON u.user_id = b.user_id;

CREATE VIEW view_open_orders AS
SELECT 
    o.order_id,
    tp.symbol,
    o.user_id,
    o.order_type,
    o.side,
    o.price,
    o.quantity,
    o.filled_quantity,
    o.status,
    o.created_at
FROM trading_orders o
JOIN trading_pairs tp ON o.pair_id = tp.pair_id
WHERE o.status = 'open';

CREATE VIEW view_recent_trades AS
SELECT 
    th.trade_id,
    tp.symbol,
    th.price,
    th.quantity,
    th.total,
    u1.username AS buyer,
    u2.username AS seller,
    th.created_at
FROM trade_history th
JOIN trading_pairs tp ON th.pair_id = tp.pair_id
JOIN users u1 ON th.buyer_id = u1.user_id
JOIN users u2 ON th.seller_id = u2.user_id
ORDER BY th.created_at DESC
LIMIT 100;

-- ============================================================
-- 8. ПРОВЕРКА
-- ============================================================

SELECT 'База данных создана успешно!' AS Status;
SELECT COUNT(*) AS total_users FROM users;
SELECT COUNT(*) AS total_orders FROM trading_orders;
SELECT COUNT(*) AS total_blocks FROM blockchain_blocks;

SHOW TABLES;