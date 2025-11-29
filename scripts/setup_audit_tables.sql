-- API Audit and Analytics Tables

-- API Call Logs (stores every API call)
CREATE TABLE IF NOT EXISTS api_call_logs (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(100),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    query_params TEXT,
    request_body TEXT,
    response_status INTEGER,
    response_time_ms FLOAT,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search Logs (specific for search queries)
CREATE TABLE IF NOT EXISTS search_logs (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(100),
    query TEXT NOT NULL,
    endpoint VARCHAR(100),
    results_count INTEGER,
    response_time_ms FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_logs_created_at ON api_call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_logs_api_key ON api_call_logs(api_key);
CREATE INDEX IF NOT EXISTS idx_api_logs_endpoint ON api_call_logs(endpoint);

CREATE INDEX IF NOT EXISTS idx_search_logs_created_at ON search_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_search_logs_api_key ON search_logs(api_key);
CREATE INDEX IF NOT EXISTS idx_search_logs_query ON search_logs(query);

-- Partitioning for performance (optional, for high volume)
-- Partition by month for better query performance
-- CREATE TABLE api_call_logs_2024_11 PARTITION OF api_call_logs
-- FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

COMMENT ON TABLE api_call_logs IS 'Stores all API calls for auditing and analytics';
COMMENT ON TABLE search_logs IS 'Stores search queries for analytics and improvement';
