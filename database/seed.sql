-- Safe starter data for local development only.
-- Do not use real learner or parent data in seed files.

-- Safe local development data only. The password for these accounts is ChangeMe123!
-- Change it before any shared or production use.

INSERT INTO schools (name, slug, motto, logo_path)
VALUES ('Siphesihle High School', 'siphesihle-high-school', 'Ukukhanya Makwande', '/frontend/assets/images/logo.jpg')
ON CONFLICT (slug) DO UPDATE SET logo_path = EXCLUDED.logo_path;

INSERT INTO users (school_id, full_name, email, student_number, employee_id, password_hash, role)
SELECT id, 'Demo Learner', 'learner@siphesihle.school', '26123456', NULL,
	   'pbkdf2_sha256$210000$AXGd_wqhNVK76n7q4DrVaw$RFQ6Olg7v-4uQk_NsUwftAYa6w3yQC0tivnUnX8cZzk', 'learner'
FROM schools WHERE slug = 'siphesihle-high-school'
ON CONFLICT (school_id, email) DO UPDATE
SET full_name = EXCLUDED.full_name,
	student_number = EXCLUDED.student_number,
	employee_id = EXCLUDED.employee_id,
	password_hash = EXCLUDED.password_hash,
	role = EXCLUDED.role;

INSERT INTO users (school_id, full_name, email, student_number, employee_id, password_hash, role)
SELECT id, 'Demo Teacher', 'teacher@siphesihle.school', NULL, 'T2347233',
	   'pbkdf2_sha256$210000$AXGd_wqhNVK76n7q4DrVaw$RFQ6Olg7v-4uQk_NsUwftAYa6w3yQC0tivnUnX8cZzk', 'teacher'
FROM schools WHERE slug = 'siphesihle-high-school'
ON CONFLICT (school_id, email) DO UPDATE
SET full_name = EXCLUDED.full_name,
	student_number = EXCLUDED.student_number,
	employee_id = EXCLUDED.employee_id,
	password_hash = EXCLUDED.password_hash,
	role = EXCLUDED.role;

INSERT INTO assessment_questions (school_id, subject, question_key, prompt, answer_key)
SELECT id, 'Economics 101', question_key, prompt, answer_key
FROM schools,
(VALUES
	('q1', 'What is the fundamental economic problem facing all societies?', 'B'),
	('q2', 'Opportunity cost is best defined as:', 'B'),
	('q3', 'Which factor of production includes natural resources used in the creation of goods?', 'C'),
	('q4', 'According to the Law of Demand, when the price of a product rises:', 'C'),
	('q5', 'The point where the demand curve and supply curve intersect is called the:', 'B'),
	('q6', 'Which market structure is characterized by a single supplier dominating the entire industry?', 'B'),
	('q7', 'Gross Domestic Product (GDP) measures:', 'B'),
	('q8', 'Microeconomics focuses primarily on:', 'B'),
	('q9', 'A sustained rise in the general price level is called:', 'C'),
	('q10', 'What type of tax takes a larger percentage of income from high-income earners?', 'C')
) AS question_data(question_key, prompt, answer_key)
WHERE slug = 'siphesihle-high-school'
ON CONFLICT (school_id, subject, question_key) DO UPDATE
SET prompt = EXCLUDED.prompt, answer_key = EXCLUDED.answer_key;
