-- 06 insert readers test data

INSERT INTO readers (full_name, email, phone, address) VALUES
('Иванов Иван Иванович', 'ivanov@example.com', '+7 (123) 456-78-90', 'ул. Ленина, д. 10, кв. 5'),
('Петрова Мария Сергеевна', 'petrova@example.com', '+7 (234) 567-89-01', 'пр. Мира, д. 25, кв. 12'),
('Сидоров Алексей Петрович', 'sidorov@example.com', '+7 (345) 678-90-12', 'ул. Советская, д. 15'),
('Козлова Елена Викторовна', 'kozlova@example.com', '+7 (456) 789-01-23', 'ул. Пушкина, д. 8, кв. 3'),
('Николаев Дмитрий Александрович', 'nikolaev@example.com', '+7 (567) 890-12-34', 'пр. Гагарина, д. 42, кв. 7')
ON CONFLICT (email) DO NOTHING;
