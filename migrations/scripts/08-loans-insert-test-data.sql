-- 08 insert loans test data

-- add active loan
INSERT INTO loans (book_id, reader_id, loan_date, due_date, status)
SELECT
    b.id,
    r.id,
    CURRENT_DATE - INTERVAL '5 days',
    CURRENT_DATE + INTERVAL '25 days',
    'active'
FROM books b
CROSS JOIN readers r
WHERE b.title = 'Мастер и Маргарита'
AND r.full_name = 'Иванов Иван Иванович'
ON CONFLICT (book_id, status) DO NOTHING;

-- add overdue loan
INSERT INTO loans (book_id, reader_id, loan_date, due_date, status)
SELECT
    b.id,
    r.id,
    CURRENT_DATE - INTERVAL '15 days',
    CURRENT_DATE - INTERVAL '5 days',
    'overdue'
FROM books b
CROSS JOIN readers r
WHERE b.title = 'Преступление и наказание'
AND r.full_name = 'Петрова Мария Сергеевна'
ON CONFLICT (book_id, status) DO NOTHING;

-- add returned loan
INSERT INTO loans (book_id, reader_id, loan_date, due_date, return_date, status)
SELECT
    b.id,
    r.id,
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE - INTERVAL '20 days',
    CURRENT_DATE - INTERVAL '19 days',
    'returned'
FROM books b
CROSS JOIN readers r
WHERE b.title = '1984'
AND r.full_name = 'Сидоров Алексей Петрович'
ON CONFLICT (book_id, status) DO NOTHING;
