-- 07 add loans table

-- loans table
CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    reader_id INTEGER NOT NULL REFERENCES readers(id) ON DELETE CASCADE,
    loan_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    return_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- 'active', 'returned', 'overdue'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_active_loan UNIQUE (book_id, status)
);

-- create unique index to check active rents
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_loan
ON loans(book_id)
WHERE status = 'active';
