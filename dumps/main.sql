-- PostgreSQL DUMP SCRIPT: ИСПРАВЛЕННАЯ ВЕРСИЯ

-- Устанавливаем последовательности в начальное состояние (Сброс ID)
SELECT setval('employee_eid_seq', 1, false);
SELECT setval('organization_unit_id_seq', 1, false);
SELECT setval('profile_id_seq', 1, false);
SELECT setval('file_id_seq', 1, false);
SELECT setval('profile_project_id_seq', 1, false);
SELECT setval('profile_vacation_id_seq', 1, false);
SELECT setval('profile_change_log_id_seq', 1, false);

-- 1. Очистка всех таблиц (в порядке, учитывающем внешние ключи)
-- CASCADE гарантирует, что зависимые таблицы также очистятся
TRUNCATE TABLE profile_change_log CASCADE; 
TRUNCATE TABLE file CASCADE; -- Очистка file первой, т.к. на нее ссылается profile
TRUNCATE TABLE profile CASCADE;
TRUNCATE TABLE employee CASCADE; 
TRUNCATE TABLE organization_unit CASCADE;

---
--- 2. ВСТАВКА ДАННЫХ В ТАБЛИЦУ 'FILE'
---
INSERT INTO file (id, name, path, created_by) VALUES 
(1, 'avatar_ivanov.jpg', '/files/avatars/100.jpg', 100),
(2, 'avatar_petrov.png', '/files/avatars/200.png', 200),
(3, 'doc_project_plan.pdf', '/files/docs/project_plan.pdf', 100);

---
--- 3. ВРЕМЕННО ОТКЛЮЧАЕМ ПРОВЕРКУ КЛЮЧЕЙ
---
-- Это критически важно для циклических и самореферентных ссылок.
-- Если Alembic не создал FK как DEFERRABLE, то этот шаг приведет к ошибке.
SET CONSTRAINTS ALL DEFERRED; 


---
--- 4. ВСТАВКА ДАННЫХ В ТАБЛИЦУ 'EMPLOYEE' (Вставляем руководителей раньше подразделений)
---
-- Вставляем минимально необходимое количество сотрудников для заполнения поля manager_eid в units.
-- EID 1: Генеральный Директор (Руководитель Департамента Финансов)
INSERT INTO employee (eid, full_name, position, work_email, birth_date, hire_date, work_band, is_fired, hrbp_eid, organization_unit) VALUES 
(1, 'Генералов Геннадий Геннадьевич', 'Генеральный Директор', 'g.generalov@bank.ru', '1970-01-01', '2000-01-01', 'A', FALSE, NULL, NULL);

-- EID 100: Руководитель ДЦТ (organization_unit=1)
INSERT INTO employee (eid, full_name, position, work_email, organization_unit, birth_date, hire_date, work_band, is_fired, hrbp_eid) VALUES 
(100, 'Иванов Иван Иванович', 'Директор Департамента', 'i.ivanov@bank.ru', NULL, '1980-05-15', '2010-06-01', 'B', FALSE, 1);

-- EID 200: Руководитель УР (organization_unit=2)
INSERT INTO employee (eid, full_name, position, work_email, organization_unit, birth_date, hire_date, work_band, is_fired, hrbp_eid) VALUES 
(200, 'Петров Петр Петрович', 'Начальник Управления', 'p.petrov@bank.ru', NULL, '1985-08-20', '2015-09-10', 'C', FALSE, 100);

-- EID 300: Руководитель ОБ (organization_unit=3)
INSERT INTO employee (eid, full_name, position, work_email, organization_unit, birth_date, hire_date, work_band, is_fired, hrbp_eid) VALUES 
(300, 'Сидоров Сергей Сергеевич', 'Начальник Отдела', 's.sidorov@bank.ru', NULL, '1990-03-25', '2018-02-15', 'D', FALSE, 100);

-- EID 400: Обычный сотрудник (organization_unit=3)
INSERT INTO employee (eid, full_name, position, work_email, organization_unit, birth_date, hire_date, work_band, is_fired, hrbp_eid) VALUES 
(400, 'Николаев Николай Николаевич', 'Старший Разработчик', 'n.nikolaev@bank.ru', NULL, '1995-12-12', '2020-01-01', 'E', FALSE, 300);


---
--- 5. ВСТАВКА ДАННЫХ В ТАБЛИЦУ 'ORGANIZATION_UNIT' (Иерархия)
---
-- ID 1: ДЕПАРТАМЕНТ (parent_id=NULL, manager_eid=100)
INSERT INTO organization_unit (id, name, unit_type, parent_id, manager_eid, is_temporary) VALUES 
(1, 'Департамент Цифровых Технологий', 'DEPARTMENT', NULL, 100, FALSE);

-- ID 2: УПРАВЛЕНИЕ (parent_id=1, manager_eid=200)
INSERT INTO organization_unit (id, name, unit_type, parent_id, manager_eid, is_temporary) VALUES 
(2, 'Управление Разработки', 'MANAGEMENT', 1, 200, FALSE);

-- ID 3: ОТДЕЛ (parent_id=2, manager_eid=300)
INSERT INTO organization_unit (id, name, unit_type, parent_id, manager_eid, is_temporary) VALUES 
(3, 'Отдел Бэкэнда', 'DIVISION', 2, 300, FALSE);

-- ID 4: ПРОЕКТНАЯ КОМАНДА (parent_id=2, manager_eid=200)
INSERT INTO organization_unit (id, name, unit_type, parent_id, manager_eid, is_temporary, start_date, end_date) VALUES 
(4, 'Проект "Срочный Релиз"', 'PROJECT_TEAM', 2, 200, TRUE, '2025-01-01', '2025-06-30');

-- ID 5: ВТОРОЙ ДЕПАРТАМЕНТ (parent_id=NULL, manager_eid=1)
INSERT INTO organization_unit (id, name, unit_type, parent_id, manager_eid, is_temporary) VALUES 
(5, 'Департамент Финансов', 'DEPARTMENT', NULL, 1, FALSE);


---
--- 6. ОБНОВЛЕНИЕ 'EMPLOYEE' (Устанавливаем organization_unit)
---
UPDATE employee SET organization_unit = 1 WHERE eid = 100;
UPDATE employee SET organization_unit = 2 WHERE eid = 200;
UPDATE employee SET organization_unit = 3 WHERE eid = 300;
UPDATE employee SET organization_unit = 3 WHERE eid = 400;
UPDATE employee SET organization_unit = 5 WHERE eid = 1;

---
--- 7. ВСТАВКА ДАННЫХ В ТАБЛИЦУ 'PROFILE' 
---
-- Все EID (100, 200, 300) теперь существуют
INSERT INTO profile (id, employee_id, avatar_id, personal_phone, telegram, about_me) VALUES 
(1, 100, 1, '+79001112233', '@i_ivanov', 'Опытный руководитель, люблю agile и кофе.'),
(2, 200, 2, '+79004445566', '@p_petrov', 'Специалист по разработке мобильных приложений.'),
(3, 300, NULL, '+79007778899', '@s_sidorov', 'Ответственный начальник, всегда на связи.');

---
--- 8. ВСТАВКА ДАННЫХ В ЗАВИСИМЫЕ ТАБЛИЦЫ
---
-- Проекты (Зависят от Profile ID)
INSERT INTO profile_project (profile_id, name, start_d, end_d, position, link) VALUES
(1, 'Обновление CRM', '2023-01-01', '2023-12-31', 'Куратор', 'http://jira/crm-upd'),
(2, 'Запуск Мобильного Банка 2.0', '2024-05-01', NULL, 'Ведущий разработчик', 'http://jira/mobile-2');

-- Отпуска (Зависят от Profile ID и Substitute EID)
INSERT INTO profile_vacation (profile_id, is_planned, start_date, end_date, substitute_eid, comment, is_official) VALUES
(2, TRUE, '2026-07-01', '2026-07-14', 300, 'Семейный отпуск, связь только по срочным вопросам.', FALSE), 
(2, FALSE, '2025-11-01', '2025-11-10', NULL, 'Учебный отпуск', TRUE); 

-- Лог изменений (Зависят от Profile ID и Changed_by EID)
INSERT INTO profile_change_log (profile_id, changed_by_eid, changed_at, table_name, record_id, field_name, old_value, new_value, operation) VALUES
(1, 100, NOW() - INTERVAL '1 day', 'profile', 1, 'personal_phone', '+79000000000', '+79001112233', 'UPDATE'),
(1, 1, NOW(), 'profile_project', NULL, 'name', NULL, '{"name": "Обновление CRM"}', 'CREATE');

---
--- 9. ВОССТАНАВЛИВАЕМ ПРОВЕРКУ КЛЮЧЕЙ
---
-- Все ограничения проверяются в конце транзакции.
SET CONSTRAINTS ALL IMMEDIATE;


-- Обновляем последовательности
SELECT setval('employee_eid_seq', (SELECT MAX(eid) FROM employee));
SELECT setval('organization_unit_id_seq', (SELECT MAX(id) FROM organization_unit));
SELECT setval('profile_id_seq', (SELECT MAX(id) FROM profile));
SELECT setval('file_id_seq', (SELECT MAX(id) FROM file));
SELECT setval('profile_project_id_seq', (SELECT MAX(id) FROM profile_project));
SELECT setval('profile_vacation_id_seq', (SELECT MAX(id) FROM profile_vacation));
SELECT setval('profile_change_log_id_seq', (SELECT MAX(id) FROM profile_change_log));