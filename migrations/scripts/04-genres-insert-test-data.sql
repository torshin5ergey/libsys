-- 04 insert genres test data

INSERT INTO genres (name, description) VALUES
('Роман', 'Повествовательное произведение с развитым сюжетом и персонажами'),
('Фантастика', 'Произведения, основанные на научных или технологических концепциях'),
('Детектив', 'Произведения о расследовании преступлений'),
('Фэнтези', 'Произведения с элементами волшебства и мифологии'),
('Классика', 'Признанные шедевры мировой литературы'),
('Антиутопия', 'Произведения, описывающие негативное будущее общество'),
('Приключения', 'Произведения о путешествиях и приключениях'),
('Детская литература', 'Произведения, предназначенные для детей'),
('Философская проза', 'Произведения с глубоким философским содержанием')
ON CONFLICT (name) DO NOTHING;

-- update books with genres
UPDATE books
SET genre_id = (SELECT id FROM genres WHERE name = 'Роман')
WHERE title IN ('Мастер и Маргарита', 'Преступление и наказание', 'Война и мир');

UPDATE books
SET genre_id = (SELECT id FROM genres WHERE name = 'Фэнтези')
WHERE title IN ('Гарри Поттер и философский камень', 'Алиса в Стране чудес');

UPDATE books
SET genre_id = (SELECT id FROM genres WHERE name = 'Детектив')
WHERE title = 'Шерлок Холмс';

UPDATE books
SET genre_id = (SELECT id FROM genres WHERE name = 'Антиутопия')
WHERE title = '1984';

UPDATE books
SET genre_id = (SELECT id FROM genres WHERE name = 'Детская литература')
WHERE title = 'Маленький принц';
