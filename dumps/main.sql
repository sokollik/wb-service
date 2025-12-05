-- PostgreSQL Test Data Dump
-- Encoding: UTF-8

-- ============================================
-- CREATE TABLES (на основе models)
-- ============================================

-- File Table
CREATE TABLE IF NOT EXISTS file (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR,
    path VARCHAR
);

-- Department Table
CREATE TABLE IF NOT EXISTS department (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    parent_id BIGINT REFERENCES department(id) ON DELETE CASCADE
);

-- Employee Table
CREATE TABLE IF NOT EXISTS employee (
    eid BIGSERIAL PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    position VARCHAR NOT NULL,
    department_id BIGINT REFERENCES department(id),
    birth_date DATE NOT NULL,
    hire_date DATE NOT NULL,
    work_phone VARCHAR,
    work_email VARCHAR NOT NULL UNIQUE,
    work_band VARCHAR,
    manager_eid BIGINT REFERENCES employee(eid),
    hrbp_eid BIGINT REFERENCES employee(eid)
);

-- Profile Table
CREATE TABLE IF NOT EXISTS profile (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT NOT NULL UNIQUE REFERENCES employee(eid) ON DELETE CASCADE,
    avatar_id BIGINT REFERENCES file(id),
    personal_phone VARCHAR,
    telegram VARCHAR,
    about_me VARCHAR(1000)
);

-- Profile Project Table
CREATE TABLE IF NOT EXISTS profile_project (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    start_d DATE,
    end_d DATE,
    position VARCHAR,
    link VARCHAR
);

-- Profile Vacation Table
CREATE TABLE IF NOT EXISTS profile_vacation (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
    is_planned BOOLEAN NOT NULL DEFAULT TRUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    substitute_eid BIGINT REFERENCES employee(eid),
    comment VARCHAR,
    is_official BOOLEAN NOT NULL DEFAULT FALSE
);

-- Profile Operation Type Enum
CREATE TYPE profile_operation_type AS ENUM ('CREATE', 'UPDATE', 'DELETE');

-- Profile Change Log Table
CREATE TABLE IF NOT EXISTS profile_change_log (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
    changed_by_eid BIGINT NOT NULL REFERENCES employee(eid),
    changed_at TIMESTAMP NOT NULL DEFAULT now(),
    table_name VARCHAR(50) NOT NULL,
    record_id BIGINT,
    field_name VARCHAR NOT NULL,
    old_value VARCHAR,
    new_value VARCHAR,
    operation profile_operation_type NOT NULL
);

-- ============================================
-- INSERT DATA
-- ============================================

-- ============================================
-- 1. Departments (Подразделения)
-- ============================================

INSERT INTO department (id, name, parent_id) VALUES
(1, 'Головной офис', NULL),
(2, 'IT департамент', 1),
(3, 'HR департамент', 1),
(4, 'Разработка', 2),
(5, 'Тестирование', 2),
(6, 'DevOps', 2),
(7, 'Рекрутмент', 3),
(8, 'Администрирование', 3);

-- Сброс sequence для department
SELECT setval('department_id_seq', (SELECT MAX(id) FROM department));

-- ============================================
-- 2. Employees (Сотрудники)
-- ============================================

INSERT INTO employee (eid, full_name, position, department_id, birth_date, hire_date, work_phone, work_email, work_band, manager_eid, hrbp_eid) VALUES
-- Руководители
(1, 'Иванов Иван Иванович', 'CEO', 1, '1975-03-15', '2010-01-10', '+7-495-123-4501', 'i.ivanov@company.com', 'E5', NULL, NULL),
(2, 'Петрова Анна Сергеевна', 'HR Director', 3, '1980-07-22', '2012-05-15', '+7-495-123-4502', 'a.petrova@company.com', 'E4', 1, NULL),
(3, 'Сидоров Петр Алексеевич', 'CTO', 2, '1978-11-30', '2011-03-20', '+7-495-123-4503', 'p.sidorov@company.com', 'E4', 1, 2),

-- IT департамент
(4, 'Кузнецов Дмитрий Владимирович', 'Team Lead', 4, '1985-05-12', '2015-08-01', '+7-495-123-4504', 'd.kuznetsov@company.com', 'E3', 3, 2),
(5, 'Смирнова Елена Игоревна', 'Senior Developer', 4, '1990-09-18', '2017-02-10', '+7-495-123-4505', 'e.smirnova@company.com', 'E2', 4, 2),
(6, 'Морозов Алексей Петрович', 'Middle Developer', 4, '1992-01-25', '2019-06-15', '+7-495-123-4506', 'a.morozov@company.com', 'E1', 4, 2),
(7, 'Волкова Мария Дмитриевна', 'Junior Developer', 4, '1995-12-03', '2021-09-01', '+7-495-123-4507', 'm.volkova@company.com', 'E0', 4, 2),

-- Тестирование
(8, 'Новиков Сергей Александрович', 'QA Lead', 5, '1987-04-08', '2016-11-20', '+7-495-123-4508', 's.novikov@company.com', 'E3', 3, 2),
(9, 'Федорова Ольга Викторовна', 'QA Engineer', 5, '1991-08-14', '2018-03-12', '+7-495-123-4509', 'o.fedorova@company.com', 'E1', 8, 2),
(10, 'Соколов Андрей Николаевич', 'QA Engineer', 5, '1993-06-21', '2020-01-15', '+7-495-123-4510', 'a.sokolov@company.com', 'E1', 8, 2),

-- DevOps
(11, 'Лебедев Михаил Юрьевич', 'DevOps Engineer', 6, '1988-10-05', '2017-07-01', '+7-495-123-4511', 'm.lebedev@company.com', 'E2', 3, 2),
(12, 'Козлова Татьяна Ивановна', 'DevOps Engineer', 6, '1994-02-28', '2020-05-20', '+7-495-123-4512', 't.kozlova@company.com', 'E1', 11, 2),

-- HR
(13, 'Васильев Николай Сергеевич', 'HR Manager', 7, '1986-07-15', '2014-10-01', '+7-495-123-4513', 'n.vasiliev@company.com', 'E2', 2, NULL),
(14, 'Романова Светлана Олеговна', 'HR Specialist', 7, '1992-11-09', '2019-04-10', '+7-495-123-4514', 's.romanova@company.com', 'E1', 13, NULL),
(15, 'Павлов Игорь Андреевич', 'Office Manager', 8, '1989-03-17', '2016-02-15', '+7-495-123-4515', 'i.pavlov@company.com', 'E1', 2, NULL),
(16, 'Полеткина Елена Никитична', 'Middle Developer', 4, '1995-12-08', '2021-10-01', '+7-995-923-4507', 'e.polet@company.com', 'E0', 4, 2);

-- Сброс sequence для employee
SELECT setval('employee_eid_seq', (SELECT MAX(eid) FROM employee));

-- ============================================
-- 3. Profiles (Профили сотрудников)
-- ============================================

INSERT INTO profile (id, employee_id, avatar_id, personal_phone, telegram, about_me) VALUES
(1, 1, NULL, '+7-916-111-1111', '@ivanov_ceo', 'Опытный руководитель с 20-летним стажем в IT индустрии. Увлекаюсь стратегическим менеджментом и инновациями.'),
(2, 2, NULL, '+7-916-222-2222', '@petrova_hr', 'HR-профессионал с фокусом на развитие корпоративной культуры и талантов. Люблю работу с людьми.'),
(3, 3, NULL, '+7-916-333-3333', '@sidorov_cto', 'Технический директор с экспертизой в масштабировании систем. Фанат чистого кода и архитектуры.'),
(4, 4, NULL, '+7-916-444-4444', '@kuznetsov_lead', 'Team Lead с опытом в Agile разработке. Практикую код-ревью и менторство. Увлекаюсь горными лыжами.'),
(5, 5, NULL, '+7-916-555-5555', '@smirnova_dev', 'Senior разработчик на Python/Django. Люблю решать сложные задачи и оптимизировать производительность.'),
(6, 6, NULL, '+7-916-666-6666', '@morozov_dev', 'Middle разработчик, специализируюсь на backend. Интересуюсь микросервисной архитектурой.'),
(7, 7, NULL, '+7-916-777-7777', '@volkova_dev', 'Junior разработчик, активно изучаю современные технологии и best practices. Люблю учиться!'),
(8, 8, NULL, '+7-916-888-8888', '@novikov_qa', 'QA Lead с опытом автоматизации тестирования. Сторонник качества на всех этапах разработки.'),
(9, 9, NULL, '+7-916-999-9999', '@fedorova_qa', 'QA инженер, специализируюсь на функциональном и регрессионном тестировании.'),
(10, 10, NULL, '+7-917-101-0101', '@sokolov_qa', 'QA инженер с опытом в нагрузочном тестировании. Изучаю автоматизацию.'),
(11, 11, NULL, '+7-917-111-1111', '@lebedev_ops', 'DevOps инженер, специализируюсь на CI/CD и контейнеризации. Kubernetes evangelist.'),
(12, 12, NULL, '+7-917-121-2121', '@kozlova_ops', 'DevOps инженер, работаю с облачными платформами и автоматизацией инфраструктуры.'),
(13, 13, NULL, '+7-917-131-3131', '@vasiliev_hr', 'HR менеджер с фокусом на рекрутинг IT специалистов. Помогаю находить лучшие таланты.'),
(14, 14, NULL, '+7-917-141-4141', '@romanova_hr', 'HR специалист, занимаюсь адаптацией новых сотрудников и корпоративными мероприятиями.'),
(15, 15, NULL, '+7-917-151-5151', '@pavlov_office', 'Office менеджер, забочусь о комфорте в офисе. Организую teambuilding мероприятия.'),
(16, 16, NULL, '+7-907-151-5151', '@polet_office', 'я помогаю сильно');


-- Сброс sequence для profile
SELECT setval('profile_id_seq', (SELECT MAX(id) FROM profile));

-- ============================================
-- 4. Profile Projects (Проекты в профилях)
-- ============================================

INSERT INTO profile_project (id, profile_id, name, start_d, end_d, position, link) VALUES
-- Проекты для Team Lead (Кузнецов)
(1, 4, 'CRM System v2.0', '2023-01-15', '2023-12-20', 'Team Lead', 'https://youtrack.company.com/issue/CRM-100'),
(2, 4, 'Mobile App Integration', '2022-06-01', '2022-11-30', 'Senior Developer', 'https://youtrack.company.com/issue/MOB-50'),
(3, 4, 'API Gateway Migration', '2024-01-10', NULL, 'Team Lead', 'https://youtrack.company.com/issue/API-200'),

-- Проекты для Senior Developer (Смирнова)
(4, 5, 'CRM System v2.0', '2023-01-15', '2023-12-20', 'Senior Developer', 'https://youtrack.company.com/issue/CRM-100'),
(5, 5, 'Payment Module', '2022-03-01', '2022-08-15', 'Middle Developer', 'https://youtrack.company.com/issue/PAY-30'),
(6, 5, 'Notification Service', '2024-02-01', NULL, 'Senior Developer', 'https://youtrack.company.com/issue/NOT-150'),

-- Проекты для Middle Developer (Морозов)
(7, 6, 'Mobile App Integration', '2022-06-01', '2022-11-30', 'Junior Developer', 'https://youtrack.company.com/issue/MOB-50'),
(8, 6, 'API Gateway Migration', '2024-01-10', NULL, 'Middle Developer', 'https://youtrack.company.com/issue/API-200'),
(9, 6, 'User Management System', '2023-05-01', '2023-10-15', 'Middle Developer', 'https://youtrack.company.com/issue/UMS-75'),

-- Проекты для Junior Developer (Волкова)
(10, 7, 'API Gateway Migration', '2024-01-10', NULL, 'Junior Developer', 'https://youtrack.company.com/issue/API-200'),
(11, 7, 'Internal Dashboard', '2023-09-01', '2024-01-20', 'Junior Developer', 'https://youtrack.company.com/issue/DASH-25'),

-- Проекты для QA (Новиков, Федорова)
(12, 8, 'Test Automation Framework', '2023-03-01', '2023-09-30', 'QA Lead', 'https://youtrack.company.com/issue/TEST-120'),
(13, 8, 'CRM System v2.0', '2023-01-15', '2023-12-20', 'QA Lead', 'https://youtrack.company.com/issue/CRM-100'),
(14, 9, 'CRM System v2.0', '2023-01-15', '2023-12-20', 'QA Engineer', 'https://youtrack.company.com/issue/CRM-100'),
(15, 9, 'Mobile App Integration', '2022-06-01', '2022-11-30', 'QA Engineer', 'https://youtrack.company.com/issue/MOB-50'),

-- Проекты для DevOps (Лебедев)
(16, 11, 'Kubernetes Migration', '2023-02-01', '2023-08-31', 'DevOps Engineer', 'https://youtrack.company.com/issue/K8S-90'),
(17, 11, 'CI/CD Pipeline Upgrade', '2024-01-05', NULL, 'DevOps Engineer', 'https://youtrack.company.com/issue/CICD-180');

-- Сброс sequence для profile_project
SELECT setval('profile_project_id_seq', (SELECT MAX(id) FROM profile_project));

-- ============================================
-- 5. Profile Vacations (Отпуска)
-- ============================================

INSERT INTO profile_vacation (id, profile_id, is_planned, start_date, end_date, substitute_eid, comment, is_official) VALUES
-- Завершенные отпуска (2024)
(1, 4, FALSE, '2024-07-01', '2024-07-14', 5, 'Летний отпуск, семейная поездка', TRUE),
(2, 5, FALSE, '2024-08-05', '2024-08-18', 6, 'Отпуск на море', TRUE),
(3, 8, FALSE, '2024-06-10', '2024-06-23', 9, 'Летний отдых', TRUE),
(4, 11, FALSE, '2024-09-01', '2024-09-14', 12, 'Отпуск в горах', TRUE),

-- Текущие отпуска (ноябрь 2024)
(5, 6, FALSE, '2024-11-20', '2024-11-30', 5, 'Короткий отпуск', TRUE),
(6, 14, FALSE, '2024-11-25', '2024-12-05', 13, 'Отпуск перед Новым Годом', TRUE),

-- Запланированные отпуска (декабрь 2024 - 2025)
(7, 4, TRUE, '2024-12-25', '2025-01-10', 5, 'Новогодние праздники', FALSE),
(8, 5, TRUE, '2024-12-28', '2025-01-08', 6, 'Новый год с семьей', FALSE),
(9, 7, TRUE, '2024-12-20', '2024-12-31', 6, 'Зимний отдых', FALSE),
(10, 8, TRUE, '2025-01-15', '2025-01-28', 9, 'Запланирован зимний отпуск', FALSE),
(11, 9, TRUE, '2025-03-01', '2025-03-14', 10, 'Весенний отпуск', FALSE),
(12, 10, TRUE, '2025-06-01', '2025-06-14', 9, 'Летний отпуск 2025', FALSE),
(13, 11, TRUE, '2025-07-15', '2025-07-28', 12, 'Запланирован отпуск летом', FALSE),
(14, 12, TRUE, '2025-08-01', '2025-08-14', 11, 'Летние каникулы', FALSE),
(15, 13, TRUE, '2025-05-10', '2025-05-23', 14, 'Майский отпуск', FALSE);

-- Сброс sequence для profile_vacation
SELECT setval('profile_vacation_id_seq', (SELECT MAX(id) FROM profile_vacation));

-- ============================================
-- 6. Profile Change Log (История изменений)
-- ============================================

INSERT INTO profile_change_log (id, profile_id, changed_by_eid, changed_at, table_name, record_id, field_name, old_value, new_value, operation) VALUES
-- Создание профилей
(1, 5, 5, '2024-01-15 10:00:00', 'profile', 5, 'about_me', NULL, 'Senior разработчик на Python/Django.', 'CREATE'),
(2, 6, 6, '2024-01-16 11:30:00', 'profile', 6, 'telegram', NULL, '@morozov_dev', 'CREATE'),

-- Обновление личной информации
(3, 5, 5, '2024-03-20 14:25:00', 'profile', 5, 'personal_phone', '+7-916-555-0000', '+7-916-555-5555', 'UPDATE'),
(4, 5, 5, '2024-03-20 14:26:00', 'profile', 5, 'about_me', 'Senior разработчик на Python/Django.', 'Senior разработчик на Python/Django. Люблю решать сложные задачи и оптимизировать производительность.', 'UPDATE'),

-- Добавление проектов
(5, 5, 4, '2024-02-01 09:00:00', 'profile_project', 6, 'name', NULL, 'Notification Service', 'CREATE'),
(6, 6, 4, '2024-01-20 10:15:00', 'profile_project', 8, 'name', NULL, 'API Gateway Migration', 'CREATE'),

-- Обновление проектов
(7, 4, 4, '2024-02-15 16:00:00', 'profile_project', 1, 'end_d', NULL, '2023-12-20', 'UPDATE'),
(8, 5, 5, '2024-03-10 13:45:00', 'profile_project', 4, 'position', 'Middle Developer', 'Senior Developer', 'UPDATE'),

-- Планирование отпусков
(9, 4, 4, '2024-10-01 11:00:00', 'profile_vacation', 7, 'start_date', NULL, '2024-12-25', 'CREATE'),
(10, 5, 5, '2024-10-05 12:30:00', 'profile_vacation', 8, 'start_date', NULL, '2024-12-28', 'CREATE'),

-- Обновление отпусков HR-ом
(11, 4, 2, '2024-11-15 10:00:00', 'profile_vacation', 7, 'is_official', 'false', 'true', 'UPDATE'),
(12, 6, 2, '2024-11-18 09:30:00', 'profile_vacation', 5, 'is_official', 'false', 'true', 'UPDATE'),

-- Изменения через Team Lead
(13, 7, 4, '2024-04-10 15:20:00', 'profile_project', 11, 'end_d', NULL, '2024-01-20', 'UPDATE'),
(14, 6, 4, '2024-05-15 11:45:00', 'profile_project', 9, 'name', 'User Management', 'User Management System', 'UPDATE'),

-- Удаление старых проектов
(15, 5, 5, '2024-06-01 10:00:00', 'profile_project', 5, 'name', 'Payment Module', NULL, 'DELETE');

-- Сброс sequence для profile_change_log
SELECT setval('profile_change_log_id_seq', (SELECT MAX(id) FROM profile_change_log));

-- ============================================
-- ИТОГИ:
-- ============================================
-- Подразделений: 8
-- Сотрудников: 15
-- Профилей: 15
-- Проектов: 17
-- Отпусков: 15
-- Записей в истории: 15
-- ============================================