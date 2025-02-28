-- Create the receipts table
CREATE TABLE IF NOT EXISTS receipts (
    id SERIAL PRIMARY KEY,
    date_of_service DATE,
    payee VARCHAR(255),
    amount DECIMAL(10, 2),
    expense_category VARCHAR(100),
    original_filename VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for common queries
CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts(date_of_service);
CREATE INDEX IF NOT EXISTS idx_receipts_payee ON receipts(payee);
CREATE INDEX IF NOT EXISTS idx_receipts_category ON receipts(expense_category);

-- Create a view for reporting
CREATE OR REPLACE VIEW receipt_summary AS
SELECT
    date_trunc('month', date_of_service) AS month,
    expense_category,
    COUNT(*) AS receipt_count,
    SUM(amount) AS total_amount
FROM
    receipts
WHERE
    date_of_service IS NOT NULL
GROUP BY
    date_trunc('month', date_of_service),
    expense_category
ORDER BY
    month DESC,
    total_amount DESC;

-- Grant privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;