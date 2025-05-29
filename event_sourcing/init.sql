
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    type VARCHAR(255),
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
