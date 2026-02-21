-- dumps/main.sql
-- Полностью рабочий файл тестовых данных (исправлены все ошибки)
-- Уникальные work_email
-- Правильный порядок: organization_unit → employee → UPDATE manager_eid → profile → связанные таблицы

SET client_min_messages TO NOTICE;
SET search_path TO public;

-- =============================================
-- 1. Организационные единицы
-- =============================================

INSERT INTO organization_unit (name, unit_type, parent_id, manager_eid, is_temporary, start_date, end_date) VALUES
('ИТ-департамент', 'DEPARTMENT', NULL, NULL, false, NULL, NULL),
('Финансовый департамент', 'DEPARTMENT', NULL, NULL, false, NULL, NULL),
('HR-департамент', 'DEPARTMENT', NULL, NULL, false, NULL, NULL),
('Департамент безопасности', 'DEPARTMENT', NULL, NULL, false, NULL, NULL);

INSERT INTO organization_unit (name, unit_type, parent_id, manager_eid, is_temporary) VALUES
('разработки цифровых продуктов', 'MANAGEMENT', (SELECT id FROM organization_unit WHERE name = 'ИТ-департамент'), NULL, false),
('технической поддержки', 'MANAGEMENT', (SELECT id FROM organization_unit WHERE name = 'ИТ-департамент'), NULL, false),
('архитектуры', 'MANAGEMENT', (SELECT id FROM organization_unit WHERE name = 'ИТ-департамент'), NULL, false),
('бухгалтерского учета', 'MANAGEMENT', (SELECT id FROM organization_unit WHERE name = 'Финансовый департамент'), NULL, false),
('бюджетирования', 'MANAGEMENT', (SELECT id FROM organization_unit WHERE name = 'Финансовый департамент'), NULL, false),
('подбора персонала', 'MANAGEMENT', (SELECT id FROM organization_unit WHERE name = 'HR-департамент'), NULL, false),
('обучения и развития', 'MANAGEMENT', (SELECT id FROM organization_unit WHERE name = 'HR-департамент'), NULL, false),
('информационной безопасности', 'MANAGEMENT', (SELECT id FROM organization_unit WHERE name = 'Департамент безопасности'), NULL, false),
('экономической безопасности', 'MANAGEMENT', (SELECT id FROM organization_unit WHERE name = 'Департамент безопасности'), NULL, false);

INSERT INTO organization_unit (name, unit_type, parent_id, manager_eid, is_temporary) VALUES
('веб-разработки', 'DIVISION', (SELECT id FROM organization_unit WHERE name = 'разработки цифровых продуктов'), NULL, false),
('мобильной разработки', 'DIVISION', (SELECT id FROM organization_unit WHERE name = 'разработки цифровых продуктов'), NULL, false),
('эксплуатации ИТ-систем', 'DIVISION', (SELECT id FROM organization_unit WHERE name = 'технической поддержки'), NULL, false),
('архитектуры', 'DIVISION', (SELECT id FROM organization_unit WHERE name = 'архитектуры' AND parent_id = (SELECT id FROM organization_unit WHERE name = 'ИТ-департамент')), NULL, false),
('расчётов', 'DIVISION', (SELECT id FROM organization_unit WHERE name = 'бухгалтерского учета'), NULL, false),
('налогового учёта', 'DIVISION', (SELECT id FROM organization_unit WHERE name = 'бухгалтерского учета'), NULL, false),
('бюджетирования', 'DIVISION', (SELECT id FROM organization_unit WHERE name = 'бюджетирования'), NULL, false),
('защиты инфраструктуры', 'DIVISION', (SELECT id FROM organization_unit WHERE name = 'информационной безопасности'), NULL, false);

INSERT INTO organization_unit (name, unit_type, parent_id, manager_eid, is_temporary) VALUES
('фронтенд', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'веб-разработки'), NULL, false),
('backend', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'веб-разработки'), NULL, false),
('iOS', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'мобильной разработки'), NULL, false),
('Android', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'мобильной разработки'), NULL, false),
('DevOps', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'эксплуатации ИТ-систем'), NULL, false),
('администрирования серверов', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'эксплуатации ИТ-систем'), NULL, false),
('enterprise-архитектуры', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'архитектуры' AND unit_type = 'DIVISION'), NULL, false),
('solution-архитектуры', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'архитектуры' AND unit_type = 'DIVISION'), NULL, false),
('зарплаты', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'расчётов'), NULL, false),
('внутренних операций', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'расчётов'), NULL, false),
('операционного бюджета', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'бюджетирования' AND unit_type = 'DIVISION'), NULL, false),
('инвестиционного бюджета', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'бюджетирования' AND unit_type = 'DIVISION'), NULL, false),
('рекрутинга', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'подбора персонала'), NULL, false),
('массового подбора', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'подбора персонала'), NULL, false),
('корпоративного обучения', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'обучения и развития'), NULL, false),
('оценки персонала', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'обучения и развития'), NULL, false),
('SOC Group', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'защиты инфраструктуры'), NULL, false),
('защиты периметра', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'защиты инфраструктуры'), NULL, false),
('проверки контрагентов', 'GROUP', (SELECT id FROM organization_unit WHERE name = 'экономической безопасности'), NULL, false);

-- =============================================
-- 2. Все сотрудники (полный список, уникальные email)
-- =============================================

INSERT INTO employee (eid, full_name, position, organization_unit, birth_date, hire_date, work_phone, work_email, work_band, hrbp_eid, is_fired) VALUES
-- Департаменты (по 2)
('3b3e359f-63a2-5b26-b0e7-6dfbc695bd5e', 'Смирнов Сергей Петрович', 'Директор ИТ-департамента', (SELECT id FROM organization_unit WHERE name = 'ИТ-департамент'), '1975-03-10', '2010-01-01', '+7(999)000-00-01', 'smirnov.sp@wb.ru', 'E1', NULL, false),
('be3950b6-ab98-5a70-9e28-07e4a67f9991', 'Иванова Ольга Николаевна', 'Зам. директора ИТ-департамента', (SELECT id FROM organization_unit WHERE name = 'ИТ-департамент'), '1978-07-22', '2012-05-15', '+7(999)000-00-02', 'ivanova.on@wb.ru', 'E2', NULL, false),
('4719193b-9bd8-50e2-a5c7-78dde63b2bb7', 'Петров Алексей Викторович', 'Финансовый директор', (SELECT id FROM organization_unit WHERE name = 'Финансовый департамент'), '1970-11-05', '2008-09-01', '+7(999)000-00-03', 'petrov.av@wb.ru', 'E1', NULL, false),
('ce5f7006-3565-56f8-9f3c-3c12e7f80e14', 'Кузнецова Елена Михайловна', 'Зам. финансового директора', (SELECT id FROM organization_unit WHERE name = 'Финансовый департамент'), '1976-04-18', '2011-03-20', '+7(999)000-00-04', 'kuznetsova.em@wb.ru', 'E2', NULL, false),
('eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', 'Васильев Дмитрий Александрович', 'Директор HR-департамента', (SELECT id FROM organization_unit WHERE name = 'HR-департамент'), '1974-08-30', '2013-02-10', '+7(999)000-00-05', 'vasilyev.da@wb.ru', 'E1', NULL, false),
('8f6b5664-e8d2-58cc-82f2-6cb356fd9784', 'Соколова Мария Сергеевна', 'Зам. директора HR-департамента', (SELECT id FROM organization_unit WHERE name = 'HR-департамент'), '1980-12-12', '2014-11-01', '+7(999)000-00-06', 'sokolova.ms@wb.ru', 'E2', NULL, false),
('dd11d7e6-2805-53a3-98c1-8642538386e1', 'Морозов Игорь Валерьевич', 'Директор департамента безопасности', (SELECT id FROM organization_unit WHERE name = 'Департамент безопасности'), '1969-01-15', '2005-06-01', '+7(999)000-00-07', 'morozov.iv@wb.ru', 'E1', NULL, false),
('87cb0a66-82a8-5199-9a3b-86ce3e1bc96a', 'Новикова Анна Петровна', 'Зам. директора по безопасности', (SELECT id FROM organization_unit WHERE name = 'Департамент безопасности'), '1977-09-25', '2010-10-10', '+7(999)000-00-08', 'novikova.ap@wb.ru', 'E2', NULL, false),

-- Управления (по 2)
('88f46b27-7a0d-551c-a970-cef765fa69be', 'Фёдоров Павел Игоревич', 'Руководитель разработки цифровых продуктов', (SELECT id FROM organization_unit WHERE name = 'разработки цифровых продуктов'), '1980-05-20', '2015-01-01', '+7(999)001-01-01', 'fedorov.pi@wb.ru', 'L3', 'eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', false),
('9430a4c8-9546-5da4-a329-dd9b78d76d2d', 'Лебедева Татьяна Викторовна', 'Зам. руководителя разработки', (SELECT id FROM organization_unit WHERE name = 'разработки цифровых продуктов'), '1983-10-08', '2017-04-15', '+7(999)001-01-02', 'lebedeva.tv@wb.ru', 'L2', 'eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', false),
('a2c5dbd0-55b3-570c-b703-5bc4d90c0df9', 'Ковалёв Артём Сергеевич', 'Руководитель технической поддержки', (SELECT id FROM organization_unit WHERE name = 'технической поддержки'), '1981-02-14', '2016-08-01', '+7(999)001-02-01', 'kovalev.as@wb.ru', 'L3', 'eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', false),
('4063fcbd-c8cc-5c79-ae04-9b414e44d220', 'Орлова Виктория Ивановна', 'Зам. руководителя техподдержки', (SELECT id FROM organization_unit WHERE name = 'технической поддержки'), '1985-11-30', '2018-09-10', '+7(999)001-02-02', 'orlova.vi@wb.ru', 'L2', 'eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', false),
('4aa04efa-b70e-5686-a51e-407ca2b7d902', 'Степанов Павел Олегович', 'Руководитель архитектуры', (SELECT id FROM organization_unit WHERE name = 'архитектуры' AND unit_type = 'MANAGEMENT'), '1979-06-18', '2014-03-01', '+7(999)001-03-01', 'stepanov.po.arch@wb.ru', 'L3', 'eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', false),
('a2066e37-36ad-5a6c-8eac-682f5302df1c', 'Жукова Мария Алексеевна', 'Зам. руководителя архитектуры', (SELECT id FROM organization_unit WHERE name = 'архитектуры' AND unit_type = 'MANAGEMENT'), '1984-09-05', '2019-11-20', '+7(999)001-03-02', 'zhukova.ma.arch@wb.ru', 'L2', 'eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', false),

-- Группы
('83dd83bc-f2ae-598f-bf99-cad03ad679b4', 'Иванов Иван Иванович', 'Senior Frontend Developer', (SELECT id FROM organization_unit WHERE name = 'фронтенд'), '1990-05-15', '2018-03-01', '+7(999)111-01-01', 'ivanov.ii@wb.ru', 'S3', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('259cec4f-fd47-504c-98e7-575539aada70', 'Петрова Анна Сергеевна', 'Middle Frontend Developer', (SELECT id FROM organization_unit WHERE name = 'фронтенд'), '1993-08-20', '2020-06-15', '+7(999)111-01-02', 'petrova.as@wb.ru', 'M2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('c748f83c-d704-56ae-b51f-36210b8a7163', 'Сидоров Алексей Петрович', 'Junior Frontend Developer', (SELECT id FROM organization_unit WHERE name = 'фронтенд'), '1997-12-10', '2023-01-10', '+7(999)111-01-03', 'sidorov.ap@wb.ru', 'J1', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('e7e6ebed-49e8-53db-b116-b433c59c403c', 'Козлова Мария Викторовна', 'Lead Frontend Developer', (SELECT id FROM organization_unit WHERE name = 'фронтенд'), '1988-03-22', '2015-09-01', '+7(999)111-01-04', 'kozlova.mv@wb.ru', 'L1', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),

('d01a2023-75b1-5e86-8bcd-cddae9027b89', 'Фёдоров Дмитрий Александрович', 'Senior Backend Developer', (SELECT id FROM organization_unit WHERE name = 'backend'), '1989-11-03', '2017-11-20', '+7(999)111-02-01', 'fedorov.da@wb.ru', 'S3', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('fc5788e2-078f-5cbe-b4ee-c44b5a26174f', 'Николаева Екатерина Павловна', 'Middle Backend Developer', (SELECT id FROM organization_unit WHERE name = 'backend'), '1994-07-14', '2021-04-05', '+7(999)111-02-02', 'nikolaeva.ep@wb.ru', 'M3', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('1c031fa7-8ef1-59ca-ac6b-dc1c90d1f91d', 'Морозов Сергей Владимирович', 'Backend Developer', (SELECT id FROM organization_unit WHERE name = 'backend'), '1996-02-28', '2022-08-15', '+7(999)111-02-03', 'morozov.sv@wb.ru', 'M1', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('f9457b5b-c4d7-5c74-bd62-f54ba2fa3c24', 'Кузнецова Ольга Игоревна', 'Lead Backend Developer', (SELECT id FROM organization_unit WHERE name = 'backend'), '1987-09-17', '2016-02-10', '+7(999)111-02-04', 'kuznetsova.oi@wb.ru', 'L2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),

('2b5e0874-fc0a-5188-abbf-1b3be5b37f55', 'Волков Павел Андреевич', 'Senior iOS Developer', (SELECT id FROM organization_unit WHERE name = 'iOS'), '1991-09-17', '2019-02-10', '+7(999)111-03-01', 'volkov.pa@wb.ru', 'S2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('2d46e835-018e-52ea-aa41-4268d2c99114', 'Лебедева Ольга Игоревна', 'Middle iOS Developer', (SELECT id FROM organization_unit WHERE name = 'iOS'), '1995-04-30', '2021-10-01', '+7(999)111-03-02', 'lebedeva.oi.ios@wb.ru', 'M2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('eb22b544-3b1c-593e-b15b-0f1923d9d4c7', 'Кузнецов Артём Денисович', 'Junior iOS Developer', (SELECT id FROM organization_unit WHERE name = 'iOS'), '1998-06-12', '2024-03-01', '+7(999)111-03-03', 'kuznetsov.ad@wb.ru', 'J2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('e3da429c-2396-5885-a555-0cb91a91d485', 'Семёнова Дарья Романовна', 'iOS Developer', (SELECT id FROM organization_unit WHERE name = 'iOS'), '1999-01-20', '2024-06-01', '+7(999)111-03-04', 'semenova.dr.ios@wb.ru', 'M1', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),

('b69d7d29-3507-5f50-8b43-83c03e73702a', 'Соколов Роман Михайлович', 'Lead Android Developer', (SELECT id FROM organization_unit WHERE name = 'Android'), '1987-01-25', '2016-05-20', '+7(999)111-04-01', 'sokolov.rm@wb.ru', 'L2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('222a96d5-66f9-5721-a1b9-79d1ff93f928', 'Попова Дарья Алексеевна', 'Senior Android Developer', (SELECT id FROM organization_unit WHERE name = 'Android'), '1992-10-08', '2019-07-15', '+7(999)111-04-02', 'popova.da@wb.ru', 'S2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('cdca04e6-8199-5197-8f8a-c5145805788a', 'Ларионов Никита Евгеньевич', 'Middle Android Developer', (SELECT id FROM organization_unit WHERE name = 'Android'), '1996-03-05', '2022-11-10', '+7(999)111-04-03', 'larionov.ne@wb.ru', 'M2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('ea94697a-93fb-5956-8532-bd86624cce8c', 'Зайцева София Дмитриевна', 'Android Developer', (SELECT id FROM organization_unit WHERE name = 'Android'), '1999-09-18', '2024-01-05', '+7(999)111-04-04', 'zaytseva.sd@wb.ru', 'M1', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),

('32be901f-3bed-57bc-9e52-13fcf4a58910', 'Григорьев Максим Олегович', 'Lead DevOps Engineer', (SELECT id FROM organization_unit WHERE name = 'DevOps'), '1986-12-14', '2015-04-01', '+7(999)111-05-01', 'grigoryev.mo@wb.ru', 'L1', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('e55d2f9e-bad1-5c29-874a-597592b5c2cd', 'Борисова Елена Андреевна', 'Senior DevOps Engineer', (SELECT id FROM organization_unit WHERE name = 'DevOps'), '1990-07-07', '2018-09-10', '+7(999)111-05-02', 'borisova.ea@wb.ru', 'S3', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('c55d19ab-43eb-5d27-a1b7-b9b1cc23c01c', 'Титов Илья Константинович', 'DevOps Engineer', (SELECT id FROM organization_unit WHERE name = 'DevOps'), '1995-05-21', '2021-12-01', '+7(999)111-05-03', 'titov.ik@wb.ru', 'M2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),

('8a4cc7f4-96b8-58a4-99a3-251545bdd9b6', 'Орлова Виктория Сергеевна', 'Senior SysAdmin', (SELECT id FROM organization_unit WHERE name = 'администрирования серверов'), '1993-02-19', '2020-03-15', '+7(999)111-06-01', 'orlova.vs.sys@wb.ru', 'S2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('a3c2d793-7a21-57aa-b68e-63acee8ab1d7', 'Макаров Даниил Романович', 'SysAdmin', (SELECT id FROM organization_unit WHERE name = 'администрирования серверов'), '1989-08-11', '2017-06-20', '+7(999)111-06-02', 'makarov.dr@wb.ru', 'M3', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('1b57032b-8896-5332-993b-df6f326fc5e2', 'Фомина Алиса Тимофеевна', 'SysAdmin', (SELECT id FROM organization_unit WHERE name = 'администрирования серверов'), '1997-11-30', '2023-05-10', '+7(999)111-06-03', 'fomina.at@wb.ru', 'M1', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),

('bd8a2475-40ea-526b-a359-6bdbae5720ca', 'Крылов Антон Вячеславович', 'Lead Enterprise Architect', (SELECT id FROM organization_unit WHERE name = 'enterprise-архитектуры'), '1985-04-05', '2014-10-01', '+7(999)111-07-01', 'krylov.av@wb.ru', 'L3', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('27564c51-dec1-5fc2-89f5-12818ea50317', 'Смирнова Наталья Юрьевна', 'Enterprise Architect', (SELECT id FROM organization_unit WHERE name = 'enterprise-архитектуры'), '1991-06-23', '2019-01-15', '+7(999)111-07-02', 'smirnova.ny@wb.ru', 'S3', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('a85598cb-2a2a-5a73-88f4-7b3c7b813a8b', 'Васильев Кирилл Андреевич', 'Enterprise Architect', (SELECT id FROM organization_unit WHERE name = 'enterprise-архитектуры'), '1992-10-17', '2020-11-10', '+7(999)111-07-03', 'vasilyev.ka.ent@wb.ru', 'S2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),

('bae201cd-557a-569a-81e0-93a794be67c1', 'Егорова Полина Максимовна', 'Lead Solution Architect', (SELECT id FROM organization_unit WHERE name = 'solution-архитектуры'), '1988-09-09', '2016-08-01', '+7(999)111-08-01', 'egorova.pm@wb.ru', 'L2', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('83ecc10e-d45a-5aef-8ed8-0f8ad307519e', 'Новиков Станислав Ильич', 'Solution Architect', (SELECT id FROM organization_unit WHERE name = 'solution-архитектуры'), '1994-12-02', '2021-03-20', '+7(999)111-08-02', 'novikov.si@wb.ru', 'S1', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),
('e7d9e3c9-78a8-57de-80bc-17cd2242ca12', 'Белова Вероника Артёмовна', 'Solution Architect', (SELECT id FROM organization_unit WHERE name = 'solution-архитектуры'), '1996-04-16', '2022-09-15', '+7(999)111-08-03', 'belova.va.sol@wb.ru', 'M3', '25a84314-dde9-5164-b07d-7a4b3a9bccb9', false),

('cc99e67d-5a82-598f-92fe-4e15a8431027', 'Андреева Ксения Борисовна', 'Старший бухгалтер по зарплате', (SELECT id FROM organization_unit WHERE name = 'зарплаты'), '1990-01-12', '2018-05-05', '+7(999)222-01-01', 'andreeva.kb@wb.ru', 'S1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('c1467ec9-7b1f-597a-afd2-4ae14772506e', 'Громов Леонид Викторович', 'Бухгалтер по зарплате', (SELECT id FROM organization_unit WHERE name = 'зарплаты'), '1987-07-28', '2015-12-01', '+7(999)222-01-02', 'gromov.lv@wb.ru', 'M3', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('d7e7714f-be1f-57d0-b5fd-11022409aeee', 'Семенова Дарья Романовна', 'Бухгалтер', (SELECT id FROM organization_unit WHERE name = 'зарплаты'), '1995-03-03', '2022-02-20', '+7(999)222-01-03', 'semenova.dr.salary@wb.ru', 'M1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),

('93e979a7-53dd-5941-a207-7acd3ff0dc7f', 'Павлов Артём Сергеевич', 'Бухгалтер внутренних операций', (SELECT id FROM organization_unit WHERE name = 'внутренних операций'), '1991-11-11', '2019-04-01', '+7(999)222-02-01', 'pavlov.as@wb.ru', 'M2', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('c3cefb61-748a-5b89-beb1-264228ed6eb8', 'Ковалёва Елизавета Дмитриевна', 'Специалист', (SELECT id FROM organization_unit WHERE name = 'внутренних операций'), '1994-08-08', '2021-07-15', '+7(999)222-02-02', 'kovaleva.ed@wb.ru', 'M1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('387f1d84-14ba-5aad-a551-a8b1707ed64a', 'Тихонов Иван Петрович', 'Старший специалист', (SELECT id FROM organization_unit WHERE name = 'внутренних операций'), '1988-05-05', '2017-10-10', '+7(999)222-02-03', 'tikhonov.ip@wb.ru', 'S2', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('154a1021-e142-5139-8b1a-0d2eb8dbbe7a', 'Медведева Анастасия Алексеевна', 'Бухгалтер', (SELECT id FROM organization_unit WHERE name = 'внутренних операций'), '1997-02-14', '2023-06-01', '+7(999)222-02-04', 'medvedeva.aa@wb.ru', 'J2', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),

('114502c3-1106-5007-a5b2-1ede529b872d', 'Орлов Дмитрий Николаевич', 'Аналитик бюджета', (SELECT id FROM organization_unit WHERE name = 'операционного бюджета'), '1989-09-09', '2018-01-20', '+7(999)222-03-01', 'orlov.dn@wb.ru', 'S1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('75f3751d-23a2-54be-8028-d91d359c5f0d', 'Лебедев Сергей Александрович', 'Финансовый аналитик', (SELECT id FROM organization_unit WHERE name = 'операционного бюджета'), '1993-12-12', '2020-09-01', '+7(999)222-03-02', 'lebedev.sa@wb.ru', 'M2', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('b6aae9e2-abe4-54f6-8024-224d8dd98126', 'Фролова Виктория Ивановна', 'Специалист по бюджету', (SELECT id FROM organization_unit WHERE name = 'операционного бюджета'), '1996-07-07', '2022-11-11', '+7(999)222-03-03', 'frolova.vi@wb.ru', 'M1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),

('2453848e-cc76-5949-b1d0-c9e67ccaa6c6', 'Смирнов Алексей Владимирович', 'Аналитик инвестиций', (SELECT id FROM organization_unit WHERE name = 'инвестиционного бюджета'), '1986-04-04', '2015-08-15', '+7(999)222-04-01', 'smirnov.av.inv@wb.ru', 'L1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('84e2945c-6cc1-5a45-80ca-f25d227e0a28', 'Кузьмина Ольга Сергеевна', 'Финансовый контролёр', (SELECT id FROM organization_unit WHERE name = 'инвестиционного бюджета'), '1990-10-10', '2019-03-03', '+7(999)222-04-02', 'kuzmina.os@wb.ru', 'S2', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('90b9d15a-b1fe-585d-a312-737e443250ec', 'Игнатов Павел Андреевич', 'Аналитик', (SELECT id FROM organization_unit WHERE name = 'инвестиционного бюджета'), '1995-01-01', '2023-04-04', '+7(999)222-04-03', 'ignatov.pa@wb.ru', 'M1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),

('25a84314-dde9-5164-b07d-7a4b3a9bccb9', 'Соловьёва Марина Викторовна', 'IT-рекрутер', (SELECT id FROM organization_unit WHERE name = 'рекрутинга'), '1992-06-15', '2020-05-10', '+7(999)333-01-01', 'soloveva.mv@wb.ru', 'M3', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('93e5274e-cf58-5fd4-b337-d4926cb880a6', 'Филиппов Никита Романович', 'Senior Recruiter', (SELECT id FROM organization_unit WHERE name = 'рекрутинга'), '1989-03-20', '2017-11-01', '+7(999)333-01-02', 'filippov.nr@wb.ru', 'S2', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('4e379796-d527-5da4-b9c3-569e8c89512d', 'Захарова Екатерина Ильинична', 'Recruiter', (SELECT id FROM organization_unit WHERE name = 'рекрутинга'), '1996-09-25', '2023-02-15', '+7(999)333-01-03', 'zakharova.ei@wb.ru', 'M1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),

('921fa4e6-b371-5f5f-8a6b-560bbe37ff1e', 'Романова София Дмитриевна', 'Специалист массового подбора', (SELECT id FROM organization_unit WHERE name = 'массового подбора'), '1994-04-18', '2021-08-20', '+7(999)333-02-01', 'romanova.sd@wb.ru', 'M2', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('c13e2865-899c-53ce-9a11-d2eaa57b2be8', 'Васнецов Артём Олегович', 'HR-специалист', (SELECT id FROM organization_unit WHERE name = 'массового подбора'), '1991-12-05', '2019-10-10', '+7(999)333-02-02', 'vasnetsov.ao@wb.ru', 'M3', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('224baa52-d8f4-5f77-8d0b-7eb73b44200b', 'Никифорова Алиса Петровна', 'Recruiter', (SELECT id FROM organization_unit WHERE name = 'массового подбора'), '1997-07-30', '2024-01-01', '+7(999)333-02-03', 'nikiforova.ap@wb.ru', 'J1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('2fff8b14-840e-571e-8e00-b0d05f0cf268', 'Гончаров Илья Сергеевич', 'Lead Mass Recruiter', (SELECT id FROM organization_unit WHERE name = 'массового подбора'), '1988-11-11', '2016-06-06', '+7(999)333-02-04', 'goncharov.is@wb.ru', 'L1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),

('810a810b-5669-59ca-84ce-e230e1b38fa3', 'Белякова Анна Михайловна', 'Тренинг-менеджер', (SELECT id FROM organization_unit WHERE name = 'корпоративного обучения'), '1990-02-28', '2018-07-15', '+7(999)333-03-01', 'belyakova.am@wb.ru', 'S1', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('a3dfe64a-ba92-5a30-ad6f-d60d39327dd9', 'Тарасов Владимир Петрович', 'Специалист по обучению', (SELECT id FROM organization_unit WHERE name = 'корпоративного обучения'), '1987-05-12', '2016-09-01', '+7(999)333-03-02', 'tarasov.vp@wb.ru', 'M3', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),
('5b881472-7e1a-5ad2-a8d2-79d63636b0af', 'Миронова Юлия Андреевна', 'L&D Specialist', (SELECT id FROM organization_unit WHERE name = 'корпоративного обучения'), '1995-10-20', '2022-03-10', '+7(999)333-03-03', 'mironova.ya@wb.ru', 'M2', '5b881472-7e1a-5ad2-a8d2-79d63636b0af', false),

('ecd6d9ec-386f-5565-bd6c-8cab7bc94685', 'Капустина Елена Николаевна', 'HR-аналитик', (SELECT id FROM organization_unit WHERE name = 'оценки персонала'), '1991-08-08', '2019-12-12', '+7(999)333-04-01', 'kapustina.en@wb.ru', 'S2', 'eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', false),
('6ebc1795-aff4-5c1a-877a-0e68dc053469', 'Суханов Дмитрий Васильевич', 'Performance Manager', (SELECT id FROM organization_unit WHERE name = 'оценки персонала'), '1989-01-15', '2017-04-05', '+7(999)333-04-02', 'sukhanov.dv@wb.ru', 'L1', 'eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', false),
('938c69ce-e25c-5403-82e3-e3feafc27022', 'Полякова Ольга Сергеевна', 'Специалист по оценке', (SELECT id FROM organization_unit WHERE name = 'оценки персонала'), '1996-11-11', '2023-08-20', '+7(999)333-04-03', 'polyakova.os@wb.ru', 'M1', 'eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', false),

('b7abbb8a-f0cb-5934-aa35-ad053ea1295d', 'Богданов Максим Александрович', 'Lead SOC Analyst', (SELECT id FROM organization_unit WHERE name = 'SOC Group'), '1988-06-20', '2016-03-15', '+7(999)444-01-01', 'bogdanov.ma@wb.ru', 'L2', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false),
('2c4fe15a-5528-5a36-8209-3f403e509e79', 'Воронина Ксения Игоревна', 'SOC Analyst L2', (SELECT id FROM organization_unit WHERE name = 'SOC Group'), '1993-09-05', '2020-11-01', '+7(999)444-01-02', 'voronina.ki@wb.ru', 'S2', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false),
('60f4898a-e471-5aa0-8ffe-2f6960bca67a', 'Ефимов Артём Владимирович', 'SOC Analyst L1', (SELECT id FROM organization_unit WHERE name = 'SOC Group'), '1997-04-10', '2023-07-01', '+7(999)444-01-03', 'efimov.av@wb.ru', 'M1', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false),

('9424fcc7-4950-52f8-8240-6c05800408b8', 'Голубев Сергей Дмитриевич', 'Network Security Engineer', (SELECT id FROM organization_unit WHERE name = 'защиты периметра'), '1990-12-12', '2018-10-10', '+7(999)444-02-01', 'golubev.sd@wb.ru', 'S3', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false),
('e276bdda-c3e2-5495-a2d3-7560df2fe37b', 'Жукова Мария Алексеевна', 'Perimeter Security Specialist', (SELECT id FROM organization_unit WHERE name = 'защиты периметра'), '1994-03-25', '2021-05-05', '+7(999)444-02-02', 'zhukova.ma.sec@wb.ru', 'M3', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false),
('bc5559c9-05e3-541f-9843-6098a2862d0a', 'Степанов Павел Олегович', 'Senior Security Engineer', (SELECT id FROM organization_unit WHERE name = 'защиты периметра'), '1987-07-18', '2015-12-20', '+7(999)444-02-03', 'stepanov.po.sec@wb.ru', 'L1', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false),

('4af6e82c-6cde-5e02-93c4-44bb5b0c4cd2', 'Лапина Дарья Сергеевна', 'Аналитик комплаенс', (SELECT id FROM organization_unit WHERE name = 'проверки контрагентов'), '1992-01-30', '2020-02-14', '+7(999)444-03-01', 'lapina.ds@wb.ru', 'M3', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false),
('cdfcb9c9-6d50-5bf0-8830-f7067a1b1746', 'Марков Николай Иванович', 'Senior Compliance Analyst', (SELECT id FROM organization_unit WHERE name = 'проверки контрагентов'), '1986-11-05', '2014-09-01', '+7(999)444-03-02', 'markov.ni@wb.ru', 'S3', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false),
('10bf16f4-fe90-53ee-914a-bc5a6e96e5d9', 'Трофимова Анастасия Петровна', 'Compliance Specialist', (SELECT id FROM organization_unit WHERE name = 'проверки контрагентов'), '1995-05-15', '2022-10-10', '+7(999)444-03-03', 'trofimova.ap@wb.ru', 'M2', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false),
('545243d2-6d4d-552d-830b-8a926e4b8476', 'Денисов Илья Андреевич', 'Аналитик', (SELECT id FROM organization_unit WHERE name = 'проверки контрагентов'), '1998-08-20', '2024-03-15', '+7(999)444-03-04', 'denisov.ia@wb.ru', 'J1', 'ecd6d9ec-386f-5565-bd6c-8cab7bc94685', false);

-- =============================================
-- 3. Назначение руководителей (после вставки сотрудников)
-- =============================================

UPDATE organization_unit SET manager_eid = 'e7e6ebed-49e8-53db-b116-b433c59c403c' WHERE name = 'фронтенд';
UPDATE organization_unit SET manager_eid = 'f9457b5b-c4d7-5c74-bd62-f54ba2fa3c24' WHERE name = 'backend';
UPDATE organization_unit SET manager_eid = 'b69d7d29-3507-5f50-8b43-83c03e73702a' WHERE name = 'Android';
UPDATE organization_unit SET manager_eid = '32be901f-3bed-57bc-9e52-13fcf4a58910' WHERE name = 'DevOps';
UPDATE organization_unit SET manager_eid = 'bd8a2475-40ea-526b-a359-6bdbae5720ca' WHERE name = 'enterprise-архитектуры';
UPDATE organization_unit SET manager_eid = 'bae201cd-557a-569a-81e0-93a794be67c1' WHERE name = 'solution-архитектуры';
UPDATE organization_unit SET manager_eid = 'b7abbb8a-f0cb-5934-aa35-ad053ea1295d' WHERE name = 'SOC Group';
UPDATE organization_unit SET manager_eid = 'bc5559c9-05e3-541f-9843-6098a2862d0a' WHERE name = 'защиты периметра';

-- =============================================
-- 4. Профили для всех сотрудников
-- =============================================

INSERT INTO profile (employee_id, personal_phone, telegram, about_me, avatar_id) VALUES
('3b3e359f-63a2-5b26-b0e7-6dfbc695bd5e', '+7(900)000-00-01', '@smirnov_sp', 'Директор ИТ-департамента', NULL),
('be3950b6-ab98-5a70-9e28-07e4a67f9991', '+7(900)000-00-02', '@ivanova_on', 'Зам. директора ИТ', NULL),
('4719193b-9bd8-50e2-a5c7-78dde63b2bb7', '+7(900)000-00-03', '@petrov_av', 'Финансовый директор', NULL),
('ce5f7006-3565-56f8-9f3c-3c12e7f80e14', '+7(900)000-00-04', '@kuznetsova_em', 'Зам. финансового директора', NULL),
('eae7c9b2-c96c-5bbc-a30e-e602fd18ef88', '+7(900)000-00-05', '@vasilyev_da', 'Директор HR', NULL),
('8f6b5664-e8d2-58cc-82f2-6cb356fd9784', '+7(900)000-00-06', '@sokolova_ms', 'Зам. директора HR', NULL),
('dd11d7e6-2805-53a3-98c1-8642538386e1', '+7(900)000-00-07', '@morozov_iv', 'Директор по безопасности', NULL),
('87cb0a66-82a8-5199-9a3b-86ce3e1bc96a', '+7(900)000-00-08', '@novikova_ap', 'Зам. по безопасности', NULL),
('88f46b27-7a0d-551c-a970-cef765fa69be', '+7(900)001-01-01', '@fedorov_pi', 'Руковожу разработкой', NULL),
('9430a4c8-9546-5da4-a329-dd9b78d76d2d', '+7(900)001-01-02', '@lebedeva_tv', 'Зам. по разработке', NULL),
('a2c5dbd0-55b3-570c-b703-5bc4d90c0df9', '+7(900)001-02-01', '@kovalev_as', 'Руковожу техподдержкой', NULL),
('4063fcbd-c8cc-5c79-ae04-9b414e44d220', '+7(900)001-02-02', '@orlova_vi', 'Зам. по техподдержке', NULL),
('4aa04efa-b70e-5686-a51e-407ca2b7d902', '+7(900)001-03-01', '@stepanov_po_arch', 'Руковожу архитектурой', NULL),
('a2066e37-36ad-5a6c-8eac-682f5302df1c', '+7(900)001-03-02', '@zhukova_ma_arch', 'Зам. по архитектуре', NULL),
('83dd83bc-f2ae-598f-bf99-cad03ad679b4', '+7(900)111-11-01', '@ivanov_ii', 'Люблю React и TypeScript', NULL),
('259cec4f-fd47-504c-98e7-575539aada70', '+7(900)111-11-02', '@petrova_as', 'Frontend разработчица', NULL),
('c748f83c-d704-56ae-b51f-36210b8a7163', '+7(900)111-11-03', '@sidorov_ap', 'Junior Frontend', NULL),
('e7e6ebed-49e8-53db-b116-b433c59c403c', '+7(900)111-11-04', '@kozlova_mv', 'Team Lead фронтенда', NULL),
('d01a2023-75b1-5e86-8bcd-cddae9027b89', '+7(900)111-11-05', '@fedorov_da', 'Senior Backend', NULL),
('fc5788e2-078f-5cbe-b4ee-c44b5a26174f', '+7(900)111-11-06', '@nikolaeva_ep', 'Middle Backend', NULL),
('1c031fa7-8ef1-59ca-ac6b-dc1c90d1f91d', '+7(900)111-11-07', '@morozov_sv', 'Backend разработчик', NULL),
('f9457b5b-c4d7-5c74-bd62-f54ba2fa3c24', '+7(900)111-11-08', '@kuznetsova_oi', 'Lead Backend', NULL),
('2b5e0874-fc0a-5188-abbf-1b3be5b37f55', '+7(900)111-11-09', '@volkov_pa', 'Senior iOS', NULL),
('2d46e835-018e-52ea-aa41-4268d2c99114', '+7(900)111-11-10', '@lebedeva_oi_ios', 'Middle iOS', NULL),
('eb22b544-3b1c-593e-b15b-0f1923d9d4c7', '+7(900)111-11-11', '@kuznetsov_ad', 'Junior iOS', NULL),
('e3da429c-2396-5885-a555-0cb91a91d485', '+7(900)111-11-12', '@semenova_dr_ios', 'iOS Developer', NULL),
('b69d7d29-3507-5f50-8b43-83c03e73702a', '+7(900)111-11-13', '@sokolov_rm', 'Lead Android', NULL),
('222a96d5-66f9-5721-a1b9-79d1ff93f928', '+7(900)111-11-14', '@popova_da', 'Senior Android', NULL),
('cdca04e6-8199-5197-8f8a-c5145805788a', '+7(900)111-11-15', '@larionov_ne', 'Middle Android', NULL),
('ea94697a-93fb-5956-8532-bd86624cce8c', '+7(900)111-11-16', '@zaytseva_sd', 'Android разработчица', NULL),
('32be901f-3bed-57bc-9e52-13fcf4a58910', '+7(900)111-11-17', '@grigoryev_mo', 'Lead DevOps', NULL),
('e55d2f9e-bad1-5c29-874a-597592b5c2cd', '+7(900)111-11-18', '@borisova_ea', 'Senior DevOps', NULL),
('c55d19ab-43eb-5d27-a1b7-b9b1cc23c01c', '+7(900)111-11-19', '@titov_ik', 'DevOps Engineer', NULL),
('8a4cc7f4-96b8-58a4-99a3-251545bdd9b6', '+7(900)111-11-20', '@orlova_vs_sys', 'Senior SysAdmin', NULL),
('a3c2d793-7a21-57aa-b68e-63acee8ab1d7', '+7(900)111-11-21', '@makarov_dr', 'SysAdmin', NULL),
('1b57032b-8896-5332-993b-df6f326fc5e2', '+7(900)111-11-22', '@fomina_at', 'SysAdmin', NULL),
('bd8a2475-40ea-526b-a359-6bdbae5720ca', '+7(900)111-11-23', '@krylov_av', 'Lead Enterprise Architect', NULL),
('27564c51-dec1-5fc2-89f5-12818ea50317', '+7(900)111-11-24', '@smirnova_ny', 'Enterprise Architect', NULL),
('a85598cb-2a2a-5a73-88f4-7b3c7b813a8b', '+7(900)111-11-25', '@vasilyev_ka_ent', 'Enterprise Architect', NULL),
('bae201cd-557a-569a-81e0-93a794be67c1', '+7(900)111-11-26', '@egorova_pm', 'Lead Solution Architect', NULL),
('83ecc10e-d45a-5aef-8ed8-0f8ad307519e', '+7(900)111-11-27', '@novikov_si', 'Solution Architect', NULL),
('e7d9e3c9-78a8-57de-80bc-17cd2242ca12', '+7(900)111-11-28', '@belova_va_sol', 'Solution Architect', NULL),
('cc99e67d-5a82-598f-92fe-4e15a8431027', '+7(900)222-22-29', '@andreeva_kb', 'Бухгалтер по зарплате', NULL),
('c1467ec9-7b1f-597a-afd2-4ae14772506e', '+7(900)222-22-30', '@gromov_lv', 'Бухгалтер', NULL),
('d7e7714f-be1f-57d0-b5fd-11022409aeee', '+7(900)222-22-31', '@semenova_dr_salary', 'Бухгалтер', NULL),
('93e979a7-53dd-5941-a207-7acd3ff0dc7f', '+7(900)222-22-32', '@pavlov_as', 'Бухгалтер внутренних операций', NULL),
('c3cefb61-748a-5b89-beb1-264228ed6eb8', '+7(900)222-22-33', '@kovaleva_ed', 'Специалист', NULL),
('387f1d84-14ba-5aad-a551-a8b1707ed64a', '+7(900)222-22-34', '@tikhonov_ip', 'Старший специалист', NULL),
('154a1021-e142-5139-8b1a-0d2eb8dbbe7a', '+7(900)222-22-35', '@medvedeva_aa', 'Бухгалтер', NULL),
('114502c3-1106-5007-a5b2-1ede529b872d', '+7(900)222-22-36', '@orlov_dn', 'Аналитик бюджета', NULL),
('75f3751d-23a2-54be-8028-d91d359c5f0d', '+7(900)222-22-37', '@lebedev_sa', 'Финансовый аналитик', NULL),
('b6aae9e2-abe4-54f6-8024-224d8dd98126', '+7(900)222-22-38', '@frolova_vi', 'Специалист по бюджету', NULL),
('2453848e-cc76-5949-b1d0-c9e67ccaa6c6', '+7(900)222-22-39', '@smirnov_av_inv', 'Аналитик инвестиций', NULL),
('84e2945c-6cc1-5a45-80ca-f25d227e0a28', '+7(900)222-22-40', '@kuzmina_os', 'Финансовый контролёр', NULL),
('90b9d15a-b1fe-585d-a312-737e443250ec', '+7(900)222-22-41', '@ignatov_pa', 'Аналитик', NULL),
('25a84314-dde9-5164-b07d-7a4b3a9bccb9', '+7(900)333-33-42', '@soloveva_mv', 'IT-рекрутер', NULL),
('93e5274e-cf58-5fd4-b337-d4926cb880a6', '+7(900)333-33-43', '@filippov_nr', 'Senior Recruiter', NULL),
('4e379796-d527-5da4-b9c3-569e8c89512d', '+7(900)333-33-44', '@zakharova_ei', 'Recruiter', NULL),
('921fa4e6-b371-5f5f-8a6b-560bbe37ff1e', '+7(900)333-33-45', '@romanova_sd', 'Специалист массового подбора', NULL),
('c13e2865-899c-53ce-9a11-d2eaa57b2be8', '+7(900)333-33-46', '@vasnetsov_ao', 'HR-специалист', NULL),
('224baa52-d8f4-5f77-8d0b-7eb73b44200b', '+7(900)333-33-47', '@nikiforova_ap', 'Recruiter', NULL),
('2fff8b14-840e-571e-8e00-b0d05f0cf268', '+7(900)333-33-48', '@goncharov_is', 'Lead Mass Recruiter', NULL),
('810a810b-5669-59ca-84ce-e230e1b38fa3', '+7(900)333-33-49', '@belyakova_am', 'Тренинг-менеджер', NULL),
('a3dfe64a-ba92-5a30-ad6f-d60d39327dd9', '+7(900)333-33-50', '@tarasov_vp', 'Специалист по обучению', NULL),
('5b881472-7e1a-5ad2-a8d2-79d63636b0af', '+7(900)333-33-51', '@mironova_ya', 'L&D Specialist', NULL),
('ecd6d9ec-386f-5565-bd6c-8cab7bc94685', '+7(900)333-33-52', '@kapustina_en', 'HR-аналитик', NULL),
('6ebc1795-aff4-5c1a-877a-0e68dc053469', '+7(900)333-33-53', '@sukhanov_dv', 'Performance Manager', NULL),
('938c69ce-e25c-5403-82e3-e3feafc27022', '+7(900)333-33-54', '@polyakova_os', 'Специалист по оценке', NULL),
('b7abbb8a-f0cb-5934-aa35-ad053ea1295d', '+7(900)444-44-55', '@bogdanov_ma', 'Lead SOC Analyst', NULL),
('2c4fe15a-5528-5a36-8209-3f403e509e79', '+7(900)444-44-56', '@voronina_ki', 'SOC Analyst L2', NULL),
('60f4898a-e471-5aa0-8ffe-2f6960bca67a', '+7(900)444-44-57', '@efimov_av', 'SOC Analyst L1', NULL),
('9424fcc7-4950-52f8-8240-6c05800408b8', '+7(900)444-44-58', '@golubev_sd', 'Network Security Engineer', NULL),
('e276bdda-c3e2-5495-a2d3-7560df2fe37b', '+7(900)444-44-59', '@zhukova_ma_sec', 'Perimeter Security Specialist', NULL),
('bc5559c9-05e3-541f-9843-6098a2862d0a', '+7(900)444-44-60', '@stepanov_po_sec', 'Senior Security Engineer', NULL),
('4af6e82c-6cde-5e02-93c4-44bb5b0c4cd2', '+7(900)444-44-61', '@lapina_ds', 'Аналитик комплаенс', NULL),
('cdfcb9c9-6d50-5bf0-8830-f7067a1b1746', '+7(900)444-44-62', '@markov_ni', 'Senior Compliance Analyst', NULL),
('10bf16f4-fe90-53ee-914a-bc5a6e96e5d9', '+7(900)444-44-63', '@trofimova_ap', 'Compliance Specialist', NULL),
('545243d2-6d4d-552d-830b-8a926e4b8476', '+7(900)444-44-64', '@denisov_ia', 'Аналитик комплаенс', NULL);

-- =============================================
-- 5. Примеры связанных таблиц
-- =============================================

INSERT INTO profile_project (profile_id, name, start_d, end_d, position, link) VALUES
((SELECT id FROM profile WHERE employee_id = '3b3e359f-63a2-5b26-b0e7-6dfbc695bd5e'), 'Цифровая трансформация банка', '2023-01-01', NULL, 'Руководитель программы', NULL),
((SELECT id FROM profile WHERE employee_id = '83dd83bc-f2ae-598f-bf99-cad03ad679b4'), 'Личный кабинет клиента', '2024-01-01', '2024-12-31', 'Frontend Developer', 'https://youtrack.wb.ru/issue/WB-1001'),
((SELECT id FROM profile WHERE employee_id = 'e7e6ebed-49e8-53db-b116-b433c59c403c'), 'Редизайн мобильного приложения', '2024-06-01', NULL, 'Tech Lead', 'https://youtrack.wb.ru/issue/WB-2004'),
((SELECT id FROM profile WHERE employee_id = 'b69d7d29-3507-5f50-8b43-83c03e73702a'), 'Android приложение WB Bank', '2023-05-01', NULL, 'Lead Android Developer', NULL);

INSERT INTO profile_vacation (profile_id, is_planned, start_date, end_date, substitute_eid, comment, is_official) VALUES
((SELECT id FROM profile WHERE employee_id = '3b3e359f-63a2-5b26-b0e7-6dfbc695bd5e'), true, '2025-07-01', '2025-07-28', 'be3950b6-ab98-5a70-9e28-07e4a67f9991', 'Летний отпуск директора ИТ', false),
((SELECT id FROM profile WHERE employee_id = '83dd83bc-f2ae-598f-bf99-cad03ad679b4'), true, '2025-08-01', '2025-08-28', '259cec4f-fd47-504c-98e7-575539aada70', 'Летний отпуск', false),
((SELECT id FROM profile WHERE employee_id = 'b69d7d29-3507-5f50-8b43-83c03e73702a'), false, '2024-12-25', '2025-01-10', '222a96d5-66f9-5721-a1b9-79d1ff93f928', 'Новогодние каникулы', true);

INSERT INTO profile_change_log (profile_id, changed_by_eid, table_name, record_id, field_name, old_value, new_value, operation) VALUES
((SELECT id FROM profile WHERE employee_id = '3b3e359f-63a2-5b26-b0e7-6dfbc695bd5e'), '3b3e359f-63a2-5b26-b0e7-6dfbc695bd5e', 'profile', (SELECT id FROM profile WHERE employee_id = '3b3e359f-63a2-5b26-b0e7-6dfbc695bd5e'), 'telegram', NULL, '@smirnov_sp', 'CREATE'),
((SELECT id FROM profile WHERE employee_id = '83dd83bc-f2ae-598f-bf99-cad03ad679b4'), '83dd83bc-f2ae-598f-bf99-cad03ad679b4', 'profile', (SELECT id FROM profile WHERE employee_id = '83dd83bc-f2ae-598f-bf99-cad03ad679b4'), 'telegram', NULL, '@ivanov_ii', 'CREATE'),
((SELECT id FROM profile WHERE employee_id = 'e7e6ebed-49e8-53db-b116-b433c59c403c'), 'e7e6ebed-49e8-53db-b116-b433c59c403c', 'profile', (SELECT id FROM profile WHERE employee_id = 'e7e6ebed-49e8-53db-b116-b433c59c403c'), 'about_me', NULL, 'Team Lead фронтенда, ментор', 'UPDATE');

INSERT INTO organization_change_log
(org_unit_id, changed_by_eid, field_name, old_value, new_value, operation)
VALUES
((SELECT id FROM organization_unit WHERE name = 'ИТ-департамент' LIMIT 1), '83dd83bc-f2ae-598f-bf99-cad03ad679b4', 'name', 'ИТ-департамент', 'Департамент цифровых технологий', 'UPDATE'),
((SELECT id FROM organization_unit WHERE name = 'Финансовый департамент' LIMIT 1), '259cec4f-fd47-504c-98e7-575539aada70', 'manager_eid', NULL, '1002', 'UPDATE'),
((SELECT id FROM organization_unit WHERE name = 'HR-департамент' LIMIT 1), 'c748f83c-d704-56ae-b51f-36210b8a7163', 'is_temporary', 'false', 'true', 'UPDATE');