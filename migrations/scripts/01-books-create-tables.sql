-- 01 create books tables

-- books table
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(255) NOT NULL,
    year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_book_title_author UNIQUE (title, author, year)
);

-- authors table
CREATE TABLE IF NOT EXISTS authors (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL UNIQUE,
    birth_year INTEGER,
    death_year INTEGER,
    nationality VARCHAR(100),
    biography TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
