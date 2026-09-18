-- PostgreSQL schema for a reusable multi-school platform.
-- Run this file after creating the school_platform database.

CREATE TABLE IF NOT EXISTS schools (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    motto VARCHAR(255),
    logo_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    full_name VARCHAR(160) NOT NULL,
    email VARCHAR(255) NOT NULL,
    student_number VARCHAR(20),
    employee_id VARCHAR(20),
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('admin', 'teacher', 'parent', 'learner')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, email)
);

CREATE TABLE IF NOT EXISTS applications (
    id BIGSERIAL PRIMARY KEY,
    school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    reference_code VARCHAR(40) NOT NULL,
    learner_name VARCHAR(160) NOT NULL,
    guardian_name VARCHAR(160) NOT NULL,
    guardian_phone VARCHAR(40) NOT NULL,
    learner_id_number VARCHAR(40) NOT NULL,
    current_school VARCHAR(160) NOT NULL,
    last_grade_passed VARCHAR(40) NOT NULL,
    prev_school_details TEXT,
    guardian_email VARCHAR(255),
    grade VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, reference_code)
);

CREATE TABLE IF NOT EXISTS application_documents (
    id BIGSERIAL PRIMARY KEY,
    application_id BIGINT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    document_type VARCHAR(30) NOT NULL CHECK (document_type IN ('learner_id', 'guardian_id', 'report_card')),
    file_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    content BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (application_id, document_type)
);

CREATE TABLE IF NOT EXISTS assessment_questions (
    id BIGSERIAL PRIMARY KEY,
    school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    subject VARCHAR(120) NOT NULL,
    question_key VARCHAR(20) NOT NULL,
    prompt TEXT NOT NULL,
    answer_key VARCHAR(10) NOT NULL,
    UNIQUE (school_id, subject, question_key)
);

CREATE TABLE IF NOT EXISTS assessments (
    id BIGSERIAL PRIMARY KEY,
    school_id BIGINT NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    learner_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(120) NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0),
    total INTEGER NOT NULL CHECK (total > 0),
    answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- These statements make the file safe to rerun against the earlier prototype schema.
ALTER TABLE users ADD COLUMN IF NOT EXISTS student_number VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS employee_id VARCHAR(20);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS learner_id_number VARCHAR(40);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS current_school VARCHAR(160);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS last_grade_passed VARCHAR(40);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS prev_school_details TEXT;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS guardian_email VARCHAR(255);
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS answers JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS users_school_role_idx ON users (school_id, role);
CREATE INDEX IF NOT EXISTS applications_school_status_idx ON applications (school_id, status);
CREATE INDEX IF NOT EXISTS assessments_learner_idx ON assessments (learner_id);
CREATE INDEX IF NOT EXISTS assessment_questions_school_subject_idx
    ON assessment_questions (school_id, subject);
CREATE UNIQUE INDEX IF NOT EXISTS users_school_student_number_idx
    ON users (school_id, student_number)
    WHERE student_number IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS users_school_employee_id_idx
    ON users (school_id, employee_id)
    WHERE employee_id IS NOT NULL;
