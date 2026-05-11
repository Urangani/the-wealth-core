CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    bid NUMERIC(28, 10),
    ask NUMERIC(28, 10),
    last NUMERIC(28, 10),
    volume NUMERIC(28, 10),
    source TEXT NOT NULL,
    PRIMARY KEY (time, symbol, source)
);

CREATE TABLE IF NOT EXISTS candles (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open NUMERIC(28, 10) NOT NULL,
    high NUMERIC(28, 10) NOT NULL,
    low NUMERIC(28, 10) NOT NULL,
    close NUMERIC(28, 10) NOT NULL,
    volume NUMERIC(28, 10) NOT NULL DEFAULT 0,
    source TEXT NOT NULL,
    PRIMARY KEY (time, symbol, timeframe, source)
);

CREATE TABLE IF NOT EXISTS features (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    feature_set TEXT NOT NULL,
    values JSONB NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (time, symbol, feature_set, source)
);

CREATE TABLE IF NOT EXISTS indicators (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    value NUMERIC(28, 10),
    values JSONB NOT NULL DEFAULT '{}'::jsonb,
    source TEXT NOT NULL,
    PRIMARY KEY (time, symbol, name, timeframe, source)
);

SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);
SELECT create_hypertable('candles', 'time', if_not_exists => TRUE);
SELECT create_hypertable('features', 'time', if_not_exists => TRUE);
SELECT create_hypertable('indicators', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON ticks (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_candles_symbol_timeframe_time ON candles (symbol, timeframe, time DESC);
CREATE INDEX IF NOT EXISTS idx_features_symbol_set_time ON features (symbol, feature_set, time DESC);
CREATE INDEX IF NOT EXISTS idx_indicators_symbol_name_time ON indicators (symbol, name, timeframe, time DESC);
