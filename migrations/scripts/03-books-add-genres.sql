--- 03 add books genres

-- create genres table
CREATE TABLE IF NOT EXISTS genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- add genre reference column to books
ALTER TABLE books
ADD COLUMN IF NOT EXISTS genre_id INTEGER REFERENCES genres(id);
