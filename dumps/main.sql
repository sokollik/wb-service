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
(1, 'Смирнов Сергей Петрович', 'Директор ИТ-департамента', (SELECT id FROM organization_unit WHERE name = 'ИТ-департамент'), '1975-03-10', '2010-01-01', '+7(999)000-00-01', 'smirnov.sp@wb.ru', 'E1', NULL, false),
(2, 'Иванова Ольга Николаевна', 'Зам. директора ИТ-департамента', (SELECT id FROM organization_unit WHERE name = 'ИТ-департамент'), '1978-07-22', '2012-05-15', '+7(999)000-00-02', 'ivanova.on@wb.ru', 'E2', NULL, false),
(3, 'Петров Алексей Викторович', 'Финансовый директор', (SELECT id FROM organization_unit WHERE name = 'Финансовый департамент'), '1970-11-05', '2008-09-01', '+7(999)000-00-03', 'petrov.av@wb.ru', 'E1', NULL, false),
(4, 'Кузнецова Елена Михайловна', 'Зам. финансового директора', (SELECT id FROM organization_unit WHERE name = 'Финансовый департамент'), '1976-04-18', '2011-03-20', '+7(999)000-00-04', 'kuznetsova.em@wb.ru', 'E2', NULL, false),
(5, 'Васильев Дмитрий Александрович', 'Директор HR-департамента', (SELECT id FROM organization_unit WHERE name = 'HR-департамент'), '1974-08-30', '2013-02-10', '+7(999)000-00-05', 'vasilyev.da@wb.ru', 'E1', NULL, false),
(6, 'Соколова Мария Сергеевна', 'Зам. директора HR-департамента', (SELECT id FROM organization_unit WHERE name = 'HR-департамент'), '1980-12-12', '2014-11-01', '+7(999)000-00-06', 'sokolova.ms@wb.ru', 'E2', NULL, false),
(7, 'Морозов Игорь Валерьевич', 'Директор департамента безопасности', (SELECT id FROM organization_unit WHERE name = 'Департамент безопасности'), '1969-01-15', '2005-06-01', '+7(999)000-00-07', 'morozov.iv@wb.ru', 'E1', NULL, false),
(8, 'Новикова Анна Петровна', 'Зам. директора по безопасности', (SELECT id FROM organization_unit WHERE name = 'Департамент безопасности'), '1977-09-25', '2010-10-10', '+7(999)000-00-08', 'novikova.ap@wb.ru', 'E2', NULL, false),

-- Управления (по 2)
(9, 'Фёдоров Павел Игоревич', 'Руководитель разработки цифровых продуктов', (SELECT id FROM organization_unit WHERE name = 'разработки цифровых продуктов'), '1980-05-20', '2015-01-01', '+7(999)001-01-01', 'fedorov.pi@wb.ru', 'L3', 5, false),
(10, 'Лебедева Татьяна Викторовна', 'Зам. руководителя разработки', (SELECT id FROM organization_unit WHERE name = 'разработки цифровых продуктов'), '1983-10-08', '2017-04-15', '+7(999)001-01-02', 'lebedeva.tv@wb.ru', 'L2', 5, false),
(11, 'Ковалёв Артём Сергеевич', 'Руководитель технической поддержки', (SELECT id FROM organization_unit WHERE name = 'технической поддержки'), '1981-02-14', '2016-08-01', '+7(999)001-02-01', 'kovalev.as@wb.ru', 'L3', 5, false),
(12, 'Орлова Виктория Ивановна', 'Зам. руководителя техподдержки', (SELECT id FROM organization_unit WHERE name = 'технической поддержки'), '1985-11-30', '2018-09-10', '+7(999)001-02-02', 'orlova.vi@wb.ru', 'L2', 5, false),
(13, 'Степанов Павел Олегович', 'Руководитель архитектуры', (SELECT id FROM organization_unit WHERE name = 'архитектуры' AND unit_type = 'MANAGEMENT'), '1979-06-18', '2014-03-01', '+7(999)001-03-01', 'stepanov.po.arch@wb.ru', 'L3', 5, false),
(14, 'Жукова Мария Алексеевна', 'Зам. руководителя архитектуры', (SELECT id FROM organization_unit WHERE name = 'архитектуры' AND unit_type = 'MANAGEMENT'), '1984-09-05', '2019-11-20', '+7(999)001-03-02', 'zhukova.ma.arch@wb.ru', 'L2', 5, false),

-- Группы
(1001, 'Иванов Иван Иванович', 'Senior Frontend Developer', (SELECT id FROM organization_unit WHERE name = 'фронтенд'), '1990-05-15', '2018-03-01', '+7(999)111-01-01', 'ivanov.ii@wb.ru', 'S3', 1042, false),
(1002, 'Петрова Анна Сергеевна', 'Middle Frontend Developer', (SELECT id FROM organization_unit WHERE name = 'фронтенд'), '1993-08-20', '2020-06-15', '+7(999)111-01-02', 'petrova.as@wb.ru', 'M2', 1042, false),
(1003, 'Сидоров Алексей Петрович', 'Junior Frontend Developer', (SELECT id FROM organization_unit WHERE name = 'фронтенд'), '1997-12-10', '2023-01-10', '+7(999)111-01-03', 'sidorov.ap@wb.ru', 'J1', 1042, false),
(1004, 'Козлова Мария Викторовна', 'Lead Frontend Developer', (SELECT id FROM organization_unit WHERE name = 'фронтенд'), '1988-03-22', '2015-09-01', '+7(999)111-01-04', 'kozlova.mv@wb.ru', 'L1', 1042, false),

(1005, 'Фёдоров Дмитрий Александрович', 'Senior Backend Developer', (SELECT id FROM organization_unit WHERE name = 'backend'), '1989-11-03', '2017-11-20', '+7(999)111-02-01', 'fedorov.da@wb.ru', 'S3', 1042, false),
(1006, 'Николаева Екатерина Павловна', 'Middle Backend Developer', (SELECT id FROM organization_unit WHERE name = 'backend'), '1994-07-14', '2021-04-05', '+7(999)111-02-02', 'nikolaeva.ep@wb.ru', 'M3', 1042, false),
(1007, 'Морозов Сергей Владимирович', 'Backend Developer', (SELECT id FROM organization_unit WHERE name = 'backend'), '1996-02-28', '2022-08-15', '+7(999)111-02-03', 'morozov.sv@wb.ru', 'M1', 1042, false),
(1008, 'Кузнецова Ольга Игоревна', 'Lead Backend Developer', (SELECT id FROM organization_unit WHERE name = 'backend'), '1987-09-17', '2016-02-10', '+7(999)111-02-04', 'kuznetsova.oi@wb.ru', 'L2', 1042, false),

(1009, 'Волков Павел Андреевич', 'Senior iOS Developer', (SELECT id FROM organization_unit WHERE name = 'iOS'), '1991-09-17', '2019-02-10', '+7(999)111-03-01', 'volkov.pa@wb.ru', 'S2', 1042, false),
(1010, 'Лебедева Ольга Игоревна', 'Middle iOS Developer', (SELECT id FROM organization_unit WHERE name = 'iOS'), '1995-04-30', '2021-10-01', '+7(999)111-03-02', 'lebedeva.oi.ios@wb.ru', 'M2', 1042, false),
(1011, 'Кузнецов Артём Денисович', 'Junior iOS Developer', (SELECT id FROM organization_unit WHERE name = 'iOS'), '1998-06-12', '2024-03-01', '+7(999)111-03-03', 'kuznetsov.ad@wb.ru', 'J2', 1042, false),
(1012, 'Семёнова Дарья Романовна', 'iOS Developer', (SELECT id FROM organization_unit WHERE name = 'iOS'), '1999-01-20', '2024-06-01', '+7(999)111-03-04', 'semenova.dr.ios@wb.ru', 'M1', 1042, false),

(1013, 'Соколов Роман Михайлович', 'Lead Android Developer', (SELECT id FROM organization_unit WHERE name = 'Android'), '1987-01-25', '2016-05-20', '+7(999)111-04-01', 'sokolov.rm@wb.ru', 'L2', 1042, false),
(1014, 'Попова Дарья Алексеевна', 'Senior Android Developer', (SELECT id FROM organization_unit WHERE name = 'Android'), '1992-10-08', '2019-07-15', '+7(999)111-04-02', 'popova.da@wb.ru', 'S2', 1042, false),
(1015, 'Ларионов Никита Евгеньевич', 'Middle Android Developer', (SELECT id FROM organization_unit WHERE name = 'Android'), '1996-03-05', '2022-11-10', '+7(999)111-04-03', 'larionov.ne@wb.ru', 'M2', 1042, false),
(1016, 'Зайцева София Дмитриевна', 'Android Developer', (SELECT id FROM organization_unit WHERE name = 'Android'), '1999-09-18', '2024-01-05', '+7(999)111-04-04', 'zaytseva.sd@wb.ru', 'M1', 1042, false),

(1017, 'Григорьев Максим Олегович', 'Lead DevOps Engineer', (SELECT id FROM organization_unit WHERE name = 'DevOps'), '1986-12-14', '2015-04-01', '+7(999)111-05-01', 'grigoryev.mo@wb.ru', 'L1', 1042, false),
(1018, 'Борисова Елена Андреевна', 'Senior DevOps Engineer', (SELECT id FROM organization_unit WHERE name = 'DevOps'), '1990-07-07', '2018-09-10', '+7(999)111-05-02', 'borisova.ea@wb.ru', 'S3', 1042, false),
(1019, 'Титов Илья Константинович', 'DevOps Engineer', (SELECT id FROM organization_unit WHERE name = 'DevOps'), '1995-05-21', '2021-12-01', '+7(999)111-05-03', 'titov.ik@wb.ru', 'M2', 1042, false),

(1020, 'Орлова Виктория Сергеевна', 'Senior SysAdmin', (SELECT id FROM organization_unit WHERE name = 'администрирования серверов'), '1993-02-19', '2020-03-15', '+7(999)111-06-01', 'orlova.vs.sys@wb.ru', 'S2', 1042, false),
(1021, 'Макаров Даниил Романович', 'SysAdmin', (SELECT id FROM organization_unit WHERE name = 'администрирования серверов'), '1989-08-11', '2017-06-20', '+7(999)111-06-02', 'makarov.dr@wb.ru', 'M3', 1042, false),
(1022, 'Фомина Алиса Тимофеевна', 'SysAdmin', (SELECT id FROM organization_unit WHERE name = 'администрирования серверов'), '1997-11-30', '2023-05-10', '+7(999)111-06-03', 'fomina.at@wb.ru', 'M1', 1042, false),

(1023, 'Крылов Антон Вячеславович', 'Lead Enterprise Architect', (SELECT id FROM organization_unit WHERE name = 'enterprise-архитектуры'), '1985-04-05', '2014-10-01', '+7(999)111-07-01', 'krylov.av@wb.ru', 'L3', 1042, false),
(1024, 'Смирнова Наталья Юрьевна', 'Enterprise Architect', (SELECT id FROM organization_unit WHERE name = 'enterprise-архитектуры'), '1991-06-23', '2019-01-15', '+7(999)111-07-02', 'smirnova.ny@wb.ru', 'S3', 1042, false),
(1025, 'Васильев Кирилл Андреевич', 'Enterprise Architect', (SELECT id FROM organization_unit WHERE name = 'enterprise-архитектуры'), '1992-10-17', '2020-11-10', '+7(999)111-07-03', 'vasilyev.ka.ent@wb.ru', 'S2', 1042, false),

(1026, 'Егорова Полина Максимовна', 'Lead Solution Architect', (SELECT id FROM organization_unit WHERE name = 'solution-архитектуры'), '1988-09-09', '2016-08-01', '+7(999)111-08-01', 'egorova.pm@wb.ru', 'L2', 1042, false),
(1027, 'Новиков Станислав Ильич', 'Solution Architect', (SELECT id FROM organization_unit WHERE name = 'solution-архитектуры'), '1994-12-02', '2021-03-20', '+7(999)111-08-02', 'novikov.si@wb.ru', 'S1', 1042, false),
(1028, 'Белова Вероника Артёмовна', 'Solution Architect', (SELECT id FROM organization_unit WHERE name = 'solution-архитектуры'), '1996-04-16', '2022-09-15', '+7(999)111-08-03', 'belova.va.sol@wb.ru', 'M3', 1042, false),

(1029, 'Андреева Ксения Борисовна', 'Старший бухгалтер по зарплате', (SELECT id FROM organization_unit WHERE name = 'зарплаты'), '1990-01-12', '2018-05-05', '+7(999)222-01-01', 'andreeva.kb@wb.ru', 'S1', 1051, false),
(1030, 'Громов Леонид Викторович', 'Бухгалтер по зарплате', (SELECT id FROM organization_unit WHERE name = 'зарплаты'), '1987-07-28', '2015-12-01', '+7(999)222-01-02', 'gromov.lv@wb.ru', 'M3', 1051, false),
(1031, 'Семенова Дарья Романовна', 'Бухгалтер', (SELECT id FROM organization_unit WHERE name = 'зарплаты'), '1995-03-03', '2022-02-20', '+7(999)222-01-03', 'semenova.dr.salary@wb.ru', 'M1', 1051, false),

(1032, 'Павлов Артём Сергеевич', 'Бухгалтер внутренних операций', (SELECT id FROM organization_unit WHERE name = 'внутренних операций'), '1991-11-11', '2019-04-01', '+7(999)222-02-01', 'pavlov.as@wb.ru', 'M2', 1051, false),
(1033, 'Ковалёва Елизавета Дмитриевна', 'Специалист', (SELECT id FROM organization_unit WHERE name = 'внутренних операций'), '1994-08-08', '2021-07-15', '+7(999)222-02-02', 'kovaleva.ed@wb.ru', 'M1', 1051, false),
(1034, 'Тихонов Иван Петрович', 'Старший специалист', (SELECT id FROM organization_unit WHERE name = 'внутренних операций'), '1988-05-05', '2017-10-10', '+7(999)222-02-03', 'tikhonov.ip@wb.ru', 'S2', 1051, false),
(1035, 'Медведева Анастасия Алексеевна', 'Бухгалтер', (SELECT id FROM organization_unit WHERE name = 'внутренних операций'), '1997-02-14', '2023-06-01', '+7(999)222-02-04', 'medvedeva.aa@wb.ru', 'J2', 1051, false),

(1036, 'Орлов Дмитрий Николаевич', 'Аналитик бюджета', (SELECT id FROM organization_unit WHERE name = 'операционного бюджета'), '1989-09-09', '2018-01-20', '+7(999)222-03-01', 'orlov.dn@wb.ru', 'S1', 1051, false),
(1037, 'Лебедев Сергей Александрович', 'Финансовый аналитик', (SELECT id FROM organization_unit WHERE name = 'операционного бюджета'), '1993-12-12', '2020-09-01', '+7(999)222-03-02', 'lebedev.sa@wb.ru', 'M2', 1051, false),
(1038, 'Фролова Виктория Ивановна', 'Специалист по бюджету', (SELECT id FROM organization_unit WHERE name = 'операционного бюджета'), '1996-07-07', '2022-11-11', '+7(999)222-03-03', 'frolova.vi@wb.ru', 'M1', 1051, false),

(1039, 'Смирнов Алексей Владимирович', 'Аналитик инвестиций', (SELECT id FROM organization_unit WHERE name = 'инвестиционного бюджета'), '1986-04-04', '2015-08-15', '+7(999)222-04-01', 'smirnov.av.inv@wb.ru', 'L1', 1051, false),
(1040, 'Кузьмина Ольга Сергеевна', 'Финансовый контролёр', (SELECT id FROM organization_unit WHERE name = 'инвестиционного бюджета'), '1990-10-10', '2019-03-03', '+7(999)222-04-02', 'kuzmina.os@wb.ru', 'S2', 1051, false),
(1041, 'Игнатов Павел Андреевич', 'Аналитик', (SELECT id FROM organization_unit WHERE name = 'инвестиционного бюджета'), '1995-01-01', '2023-04-04', '+7(999)222-04-03', 'ignatov.pa@wb.ru', 'M1', 1051, false),

(1042, 'Соловьёва Марина Викторовна', 'IT-рекрутер', (SELECT id FROM organization_unit WHERE name = 'рекрутинга'), '1992-06-15', '2020-05-10', '+7(999)333-01-01', 'soloveva.mv@wb.ru', 'M3', 1051, false),
(1043, 'Филиппов Никита Романович', 'Senior Recruiter', (SELECT id FROM organization_unit WHERE name = 'рекрутинга'), '1989-03-20', '2017-11-01', '+7(999)333-01-02', 'filippov.nr@wb.ru', 'S2', 1051, false),
(1044, 'Захарова Екатерина Ильинична', 'Recruiter', (SELECT id FROM organization_unit WHERE name = 'рекрутинга'), '1996-09-25', '2023-02-15', '+7(999)333-01-03', 'zakharova.ei@wb.ru', 'M1', 1051, false),

(1045, 'Романова София Дмитриевна', 'Специалист массового подбора', (SELECT id FROM organization_unit WHERE name = 'массового подбора'), '1994-04-18', '2021-08-20', '+7(999)333-02-01', 'romanova.sd@wb.ru', 'M2', 1051, false),
(1046, 'Васнецов Артём Олегович', 'HR-специалист', (SELECT id FROM organization_unit WHERE name = 'массового подбора'), '1991-12-05', '2019-10-10', '+7(999)333-02-02', 'vasnetsov.ao@wb.ru', 'M3', 1051, false),
(1047, 'Никифорова Алиса Петровна', 'Recruiter', (SELECT id FROM organization_unit WHERE name = 'массового подбора'), '1997-07-30', '2024-01-01', '+7(999)333-02-03', 'nikiforova.ap@wb.ru', 'J1', 1051, false),
(1048, 'Гончаров Илья Сергеевич', 'Lead Mass Recruiter', (SELECT id FROM organization_unit WHERE name = 'массового подбора'), '1988-11-11', '2016-06-06', '+7(999)333-02-04', 'goncharov.is@wb.ru', 'L1', 1051, false),

(1049, 'Белякова Анна Михайловна', 'Тренинг-менеджер', (SELECT id FROM organization_unit WHERE name = 'корпоративного обучения'), '1990-02-28', '2018-07-15', '+7(999)333-03-01', 'belyakova.am@wb.ru', 'S1', 1051, false),
(1050, 'Тарасов Владимир Петрович', 'Специалист по обучению', (SELECT id FROM organization_unit WHERE name = 'корпоративного обучения'), '1987-05-12', '2016-09-01', '+7(999)333-03-02', 'tarasov.vp@wb.ru', 'M3', 1051, false),
(1051, 'Миронова Юлия Андреевна', 'L&D Specialist', (SELECT id FROM organization_unit WHERE name = 'корпоративного обучения'), '1995-10-20', '2022-03-10', '+7(999)333-03-03', 'mironova.ya@wb.ru', 'M2', 1051, false),

(1052, 'Капустина Елена Николаевна', 'HR-аналитик', (SELECT id FROM organization_unit WHERE name = 'оценки персонала'), '1991-08-08', '2019-12-12', '+7(999)333-04-01', 'kapustina.en@wb.ru', 'S2', 5, false),
(1053, 'Суханов Дмитрий Васильевич', 'Performance Manager', (SELECT id FROM organization_unit WHERE name = 'оценки персонала'), '1989-01-15', '2017-04-05', '+7(999)333-04-02', 'sukhanov.dv@wb.ru', 'L1', 5, false),
(1054, 'Полякова Ольга Сергеевна', 'Специалист по оценке', (SELECT id FROM organization_unit WHERE name = 'оценки персонала'), '1996-11-11', '2023-08-20', '+7(999)333-04-03', 'polyakova.os@wb.ru', 'M1', 5, false),

(1055, 'Богданов Максим Александрович', 'Lead SOC Analyst', (SELECT id FROM organization_unit WHERE name = 'SOC Group'), '1988-06-20', '2016-03-15', '+7(999)444-01-01', 'bogdanov.ma@wb.ru', 'L2', 1052, false),
(1056, 'Воронина Ксения Игоревна', 'SOC Analyst L2', (SELECT id FROM organization_unit WHERE name = 'SOC Group'), '1993-09-05', '2020-11-01', '+7(999)444-01-02', 'voronina.ki@wb.ru', 'S2', 1052, false),
(1057, 'Ефимов Артём Владимирович', 'SOC Analyst L1', (SELECT id FROM organization_unit WHERE name = 'SOC Group'), '1997-04-10', '2023-07-01', '+7(999)444-01-03', 'efimov.av@wb.ru', 'M1', 1052, false),

(1058, 'Голубев Сергей Дмитриевич', 'Network Security Engineer', (SELECT id FROM organization_unit WHERE name = 'защиты периметра'), '1990-12-12', '2018-10-10', '+7(999)444-02-01', 'golubev.sd@wb.ru', 'S3', 1052, false),
(1059, 'Жукова Мария Алексеевна', 'Perimeter Security Specialist', (SELECT id FROM organization_unit WHERE name = 'защиты периметра'), '1994-03-25', '2021-05-05', '+7(999)444-02-02', 'zhukova.ma.sec@wb.ru', 'M3', 1052, false),
(1060, 'Степанов Павел Олегович', 'Senior Security Engineer', (SELECT id FROM organization_unit WHERE name = 'защиты периметра'), '1987-07-18', '2015-12-20', '+7(999)444-02-03', 'stepanov.po.sec@wb.ru', 'L1', 1052, false),

(1061, 'Лапина Дарья Сергеевна', 'Аналитик комплаенс', (SELECT id FROM organization_unit WHERE name = 'проверки контрагентов'), '1992-01-30', '2020-02-14', '+7(999)444-03-01', 'lapina.ds@wb.ru', 'M3', 1052, false),
(1062, 'Марков Николай Иванович', 'Senior Compliance Analyst', (SELECT id FROM organization_unit WHERE name = 'проверки контрагентов'), '1986-11-05', '2014-09-01', '+7(999)444-03-02', 'markov.ni@wb.ru', 'S3', 1052, false),
(1063, 'Трофимова Анастасия Петровна', 'Compliance Specialist', (SELECT id FROM organization_unit WHERE name = 'проверки контрагентов'), '1995-05-15', '2022-10-10', '+7(999)444-03-03', 'trofimova.ap@wb.ru', 'M2', 1052, false),
(1064, 'Денисов Илья Андреевич', 'Аналитик', (SELECT id FROM organization_unit WHERE name = 'проверки контрагентов'), '1998-08-20', '2024-03-15', '+7(999)444-03-04', 'denisov.ia@wb.ru', 'J1', 1052, false);

-- =============================================
-- 3. Назначение руководителей (после вставки сотрудников)
-- =============================================

UPDATE organization_unit SET manager_eid = 1004 WHERE name = 'фронтенд';
UPDATE organization_unit SET manager_eid = 1008 WHERE name = 'backend';
UPDATE organization_unit SET manager_eid = 1013 WHERE name = 'Android';
UPDATE organization_unit SET manager_eid = 1017 WHERE name = 'DevOps';
UPDATE organization_unit SET manager_eid = 1023 WHERE name = 'enterprise-архитектуры';
UPDATE organization_unit SET manager_eid = 1026 WHERE name = 'solution-архитектуры';
UPDATE organization_unit SET manager_eid = 1055 WHERE name = 'SOC Group';
UPDATE organization_unit SET manager_eid = 1060 WHERE name = 'защиты периметра';

-- =============================================
-- 4. Профили для всех сотрудников
-- =============================================

INSERT INTO profile (employee_id, personal_phone, telegram, about_me, avatar_id) VALUES
(1, '+7(900)000-00-01', '@smirnov_sp', 'Директор ИТ-департамента', NULL),
(2, '+7(900)000-00-02', '@ivanova_on', 'Зам. директора ИТ', NULL),
(3, '+7(900)000-00-03', '@petrov_av', 'Финансовый директор', NULL),
(4, '+7(900)000-00-04', '@kuznetsova_em', 'Зам. финансового директора', NULL),
(5, '+7(900)000-00-05', '@vasilyev_da', 'Директор HR', NULL),
(6, '+7(900)000-00-06', '@sokolova_ms', 'Зам. директора HR', NULL),
(7, '+7(900)000-00-07', '@morozov_iv', 'Директор по безопасности', NULL),
(8, '+7(900)000-00-08', '@novikova_ap', 'Зам. по безопасности', NULL),
(9, '+7(900)001-01-01', '@fedorov_pi', 'Руковожу разработкой', NULL),
(10, '+7(900)001-01-02', '@lebedeva_tv', 'Зам. по разработке', NULL),
(11, '+7(900)001-02-01', '@kovalev_as', 'Руковожу техподдержкой', NULL),
(12, '+7(900)001-02-02', '@orlova_vi', 'Зам. по техподдержке', NULL),
(13, '+7(900)001-03-01', '@stepanov_po_arch', 'Руковожу архитектурой', NULL),
(14, '+7(900)001-03-02', '@zhukova_ma_arch', 'Зам. по архитектуре', NULL),
(1001, '+7(900)111-11-01', '@ivanov_ii', 'Люблю React и TypeScript', NULL),
(1002, '+7(900)111-11-02', '@petrova_as', 'Frontend разработчица', NULL),
(1003, '+7(900)111-11-03', '@sidorov_ap', 'Junior Frontend', NULL),
(1004, '+7(900)111-11-04', '@kozlova_mv', 'Team Lead фронтенда', NULL),
(1005, '+7(900)111-11-05', '@fedorov_da', 'Senior Backend', NULL),
(1006, '+7(900)111-11-06', '@nikolaeva_ep', 'Middle Backend', NULL),
(1007, '+7(900)111-11-07', '@morozov_sv', 'Backend разработчик', NULL),
(1008, '+7(900)111-11-08', '@kuznetsova_oi', 'Lead Backend', NULL),
(1009, '+7(900)111-11-09', '@volkov_pa', 'Senior iOS', NULL),
(1010, '+7(900)111-11-10', '@lebedeva_oi_ios', 'Middle iOS', NULL),
(1011, '+7(900)111-11-11', '@kuznetsov_ad', 'Junior iOS', NULL),
(1012, '+7(900)111-11-12', '@semenova_dr_ios', 'iOS Developer', NULL),
(1013, '+7(900)111-11-13', '@sokolov_rm', 'Lead Android', NULL),
(1014, '+7(900)111-11-14', '@popova_da', 'Senior Android', NULL),
(1015, '+7(900)111-11-15', '@larionov_ne', 'Middle Android', NULL),
(1016, '+7(900)111-11-16', '@zaytseva_sd', 'Android разработчица', NULL),
(1017, '+7(900)111-11-17', '@grigoryev_mo', 'Lead DevOps', NULL),
(1018, '+7(900)111-11-18', '@borisova_ea', 'Senior DevOps', NULL),
(1019, '+7(900)111-11-19', '@titov_ik', 'DevOps Engineer', NULL),
(1020, '+7(900)111-11-20', '@orlova_vs_sys', 'Senior SysAdmin', NULL),
(1021, '+7(900)111-11-21', '@makarov_dr', 'SysAdmin', NULL),
(1022, '+7(900)111-11-22', '@fomina_at', 'SysAdmin', NULL),
(1023, '+7(900)111-11-23', '@krylov_av', 'Lead Enterprise Architect', NULL),
(1024, '+7(900)111-11-24', '@smirnova_ny', 'Enterprise Architect', NULL),
(1025, '+7(900)111-11-25', '@vasilyev_ka_ent', 'Enterprise Architect', NULL),
(1026, '+7(900)111-11-26', '@egorova_pm', 'Lead Solution Architect', NULL),
(1027, '+7(900)111-11-27', '@novikov_si', 'Solution Architect', NULL),
(1028, '+7(900)111-11-28', '@belova_va_sol', 'Solution Architect', NULL),
(1029, '+7(900)222-22-29', '@andreeva_kb', 'Бухгалтер по зарплате', NULL),
(1030, '+7(900)222-22-30', '@gromov_lv', 'Бухгалтер', NULL),
(1031, '+7(900)222-22-31', '@semenova_dr_salary', 'Бухгалтер', NULL),
(1032, '+7(900)222-22-32', '@pavlov_as', 'Бухгалтер внутренних операций', NULL),
(1033, '+7(900)222-22-33', '@kovaleva_ed', 'Специалист', NULL),
(1034, '+7(900)222-22-34', '@tikhonov_ip', 'Старший специалист', NULL),
(1035, '+7(900)222-22-35', '@medvedeva_aa', 'Бухгалтер', NULL),
(1036, '+7(900)222-22-36', '@orlov_dn', 'Аналитик бюджета', NULL),
(1037, '+7(900)222-22-37', '@lebedev_sa', 'Финансовый аналитик', NULL),
(1038, '+7(900)222-22-38', '@frolova_vi', 'Специалист по бюджету', NULL),
(1039, '+7(900)222-22-39', '@smirnov_av_inv', 'Аналитик инвестиций', NULL),
(1040, '+7(900)222-22-40', '@kuzmina_os', 'Финансовый контролёр', NULL),
(1041, '+7(900)222-22-41', '@ignatov_pa', 'Аналитик', NULL),
(1042, '+7(900)333-33-42', '@soloveva_mv', 'IT-рекрутер', NULL),
(1043, '+7(900)333-33-43', '@filippov_nr', 'Senior Recruiter', NULL),
(1044, '+7(900)333-33-44', '@zakharova_ei', 'Recruiter', NULL),
(1045, '+7(900)333-33-45', '@romanova_sd', 'Специалист массового подбора', NULL),
(1046, '+7(900)333-33-46', '@vasnetsov_ao', 'HR-специалист', NULL),
(1047, '+7(900)333-33-47', '@nikiforova_ap', 'Recruiter', NULL),
(1048, '+7(900)333-33-48', '@goncharov_is', 'Lead Mass Recruiter', NULL),
(1049, '+7(900)333-33-49', '@belyakova_am', 'Тренинг-менеджер', NULL),
(1050, '+7(900)333-33-50', '@tarasov_vp', 'Специалист по обучению', NULL),
(1051, '+7(900)333-33-51', '@mironova_ya', 'L&D Specialist', NULL),
(1052, '+7(900)333-33-52', '@kapustina_en', 'HR-аналитик', NULL),
(1053, '+7(900)333-33-53', '@sukhanov_dv', 'Performance Manager', NULL),
(1054, '+7(900)333-33-54', '@polyakova_os', 'Специалист по оценке', NULL),
(1055, '+7(900)444-44-55', '@bogdanov_ma', 'Lead SOC Analyst', NULL),
(1056, '+7(900)444-44-56', '@voronina_ki', 'SOC Analyst L2', NULL),
(1057, '+7(900)444-44-57', '@efimov_av', 'SOC Analyst L1', NULL),
(1058, '+7(900)444-44-58', '@golubev_sd', 'Network Security Engineer', NULL),
(1059, '+7(900)444-44-59', '@zhukova_ma_sec', 'Perimeter Security Specialist', NULL),
(1060, '+7(900)444-44-60', '@stepanov_po_sec', 'Senior Security Engineer', NULL),
(1061, '+7(900)444-44-61', '@lapina_ds', 'Аналитик комплаенс', NULL),
(1062, '+7(900)444-44-62', '@markov_ni', 'Senior Compliance Analyst', NULL),
(1063, '+7(900)444-44-63', '@trofimova_ap', 'Compliance Specialist', NULL),
(1064, '+7(900)444-44-64', '@denisov_ia', 'Аналитик комплаенс', NULL);

-- =============================================
-- 5. Примеры связанных таблиц
-- =============================================

INSERT INTO profile_project (profile_id, name, start_d, end_d, position, link) VALUES
((SELECT id FROM profile WHERE employee_id = 1), 'Цифровая трансформация банка', '2023-01-01', NULL, 'Руководитель программы', NULL),
((SELECT id FROM profile WHERE employee_id = 1001), 'Личный кабинет клиента', '2024-01-01', '2024-12-31', 'Frontend Developer', 'https://youtrack.wb.ru/issue/WB-1001'),
((SELECT id FROM profile WHERE employee_id = 1004), 'Редизайн мобильного приложения', '2024-06-01', NULL, 'Tech Lead', 'https://youtrack.wb.ru/issue/WB-2004'),
((SELECT id FROM profile WHERE employee_id = 1013), 'Android приложение WB Bank', '2023-05-01', NULL, 'Lead Android Developer', NULL);

INSERT INTO profile_vacation (profile_id, is_planned, start_date, end_date, substitute_eid, comment, is_official) VALUES
((SELECT id FROM profile WHERE employee_id = 1), true, '2025-07-01', '2025-07-28', 2, 'Летний отпуск директора ИТ', false),
((SELECT id FROM profile WHERE employee_id = 1001), true, '2025-08-01', '2025-08-28', 1002, 'Летний отпуск', false),
((SELECT id FROM profile WHERE employee_id = 1013), false, '2024-12-25', '2025-01-10', 1014, 'Новогодние каникулы', true);

INSERT INTO profile_change_log (profile_id, changed_by_eid, table_name, record_id, field_name, old_value, new_value, operation) VALUES
((SELECT id FROM profile WHERE employee_id = 1), 1, 'profile', (SELECT id FROM profile WHERE employee_id = 1), 'telegram', NULL, '@smirnov_sp', 'CREATE'),
((SELECT id FROM profile WHERE employee_id = 1001), 1001, 'profile', (SELECT id FROM profile WHERE employee_id = 1001), 'telegram', NULL, '@ivanov_ii', 'CREATE'),
((SELECT id FROM profile WHERE employee_id = 1004), 1004, 'profile', (SELECT id FROM profile WHERE employee_id = 1004), 'about_me', NULL, 'Team Lead фронтенда, ментор', 'UPDATE');