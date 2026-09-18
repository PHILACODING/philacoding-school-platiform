from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from psycopg import Connection
from psycopg.types.json import Jsonb

from ..db import get_connection
from ..schemas import AssessmentSubmission, LoginRequest, StatusUpdate
from ..security import create_access_token, require_token, verify_password

router = APIRouter()
ConnectionDependency = Annotated[Connection, Depends(get_connection)]
TokenDependency = Annotated[dict[str, int | str], Depends(require_token)]
_ALLOWED_DOCUMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
_MAX_DOCUMENT_BYTES = 5 * 1024 * 1024


@router.get("/schools")
def list_schools(connection: ConnectionDependency) -> dict[str, list[dict[str, object]]]:
    rows = connection.execute(
        "SELECT id, name, slug, motto, logo_path FROM schools ORDER BY name"
    ).fetchall()
    return {"schools": [dict(row) for row in rows]}


@router.post("/auth/login")
def login(payload: LoginRequest, connection: ConnectionDependency) -> dict[str, object]:
    user = connection.execute(
        """
        SELECT id, school_id, full_name, email, student_number, employee_id, password_hash, role
        FROM users
        WHERE school_id = (SELECT id FROM schools WHERE slug = %s)
          AND (email = %s OR student_number = %s OR employee_id = %s)
        """,
        (payload.school_slug, payload.identifier, payload.identifier, payload.identifier),
    ).fetchone()
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login details")

    return {
        "access_token": create_access_token(user["id"], user["school_id"], user["role"]),
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "student_number": user["student_number"],
            "employee_id": user["employee_id"],
            "role": user["role"],
        },
    }


@router.post("/applications", status_code=status.HTTP_201_CREATED)
def create_application(
    connection: ConnectionDependency,
    school_slug: Annotated[str, Form()],
    first_name: Annotated[str, Form()],
    surname: Annotated[str, Form()],
    id_number: Annotated[str, Form()],
    applying_grade: Annotated[str, Form()],
    current_school: Annotated[str, Form()],
    last_grade_passed: Annotated[str, Form()],
    parent_name: Annotated[str, Form()],
    parent_contact: Annotated[str, Form()],
    parent_email: Annotated[str, Form()] = "",
    prev_school_details: Annotated[str, Form()] = "",
    learner_id_document: Annotated[UploadFile, File()] = None,
    parent_id_document: Annotated[UploadFile, File()] = None,
    report_card_document: Annotated[UploadFile, File()] = None,
) -> dict[str, object]:
    school = connection.execute("SELECT id FROM schools WHERE slug = %s", (school_slug,)).fetchone()
    if not school:
        raise HTTPException(status_code=404, detail="School was not found")

    reference_code = _new_reference_code(connection)
    application = connection.execute(
        """
        INSERT INTO applications (
            school_id, reference_code, learner_name, guardian_name, guardian_phone,
            learner_id_number, current_school, last_grade_passed, prev_school_details, guardian_email, grade
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULLIF(%s, ''), NULLIF(%s, ''), %s)
        RETURNING id, reference_code, status, created_at
        """,
        (
            school["id"], reference_code, f"{first_name.strip()} {surname.strip()}", parent_name.strip(),
            parent_contact.strip(), id_number.strip(), current_school.strip(), last_grade_passed.strip(),
            prev_school_details.strip(), parent_email.strip(), applying_grade.strip(),
        ),
    ).fetchone()

    documents = {
        "learner_id": learner_id_document,
        "guardian_id": parent_id_document,
        "report_card": report_card_document,
    }
    for document_type, upload in documents.items():
        if upload is None:
            raise HTTPException(status_code=400, detail=f"Missing {document_type} document")
        content_type = upload.content_type or "application/octet-stream"
        if content_type not in _ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(status_code=400, detail="Documents must be PDF, JPG, or PNG files")
        content = upload.file.read(_MAX_DOCUMENT_BYTES + 1)
        if len(content) > _MAX_DOCUMENT_BYTES:
            raise HTTPException(status_code=413, detail="Each document must be 5 MB or smaller")
        connection.execute(
            """
            INSERT INTO application_documents
                (application_id, document_type, file_name, content_type, content)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (application["id"], document_type, upload.filename or document_type, content_type, content),
        )

    return _serialize_application(application)


@router.get("/applications")
def list_applications(connection: ConnectionDependency, token: TokenDependency) -> dict[str, list[dict[str, object]]]:
    _require_staff(token)
    rows = connection.execute(
        """
        SELECT id, reference_code, learner_name, guardian_name, guardian_phone,
               learner_id_number, current_school, last_grade_passed, prev_school_details, guardian_email,
               grade, status, created_at
        FROM applications WHERE school_id = %s ORDER BY created_at DESC
        """,
        (token["school_id"],),
    ).fetchall()
    return {"applications": [_serialize_application(row) for row in rows]}


@router.patch("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    payload: StatusUpdate,
    connection: ConnectionDependency,
    token: TokenDependency,
) -> dict[str, object]:
    _require_staff(token)
    row = connection.execute(
        """
        UPDATE applications SET status = %s
        WHERE id = %s AND school_id = %s
        RETURNING id, reference_code, status, created_at
        """,
        (payload.status, application_id, token["school_id"]),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Application was not found")
    return _serialize_application(row)


@router.post("/assessments/submit", status_code=status.HTTP_201_CREATED)
def submit_assessment(
    payload: AssessmentSubmission,
    connection: ConnectionDependency,
    token: TokenDependency,
) -> dict[str, object]:
    if token["role"] != "learner":
        raise HTTPException(status_code=403, detail="Only learners can submit assessments")
    if payload.school_slug != _school_slug(connection, int(token["school_id"])):
        raise HTTPException(status_code=403, detail="School access mismatch")

    recent_submission = connection.execute(
        """
        SELECT 1
        FROM assessments
        WHERE school_id = %s AND learner_id = %s
          AND submitted_at >= NOW() - INTERVAL '24 hours'
        LIMIT 1
        """,
        (token["school_id"], token["sub"]),
    ).fetchone()
    if recent_submission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only one assessment may be submitted every 24 hours",
        )

    questions = connection.execute(
        """
        SELECT question_key, answer_key FROM assessment_questions
        WHERE school_id = %s AND subject = %s
        ORDER BY id
        """,
        (token["school_id"], payload.subject),
    ).fetchall()
    if not questions:
        raise HTTPException(status_code=404, detail="Assessment was not found")

    score = sum(payload.answers.get(row["question_key"]) == row["answer_key"] for row in questions)
    result = connection.execute(
        """
        INSERT INTO assessments (school_id, learner_id, subject, score, total, answers)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, subject, score, total, submitted_at
        """,
        (token["school_id"], token["sub"], payload.subject, score, len(questions), Jsonb(payload.answers)),
    ).fetchone()
    return {
        "id": result["id"], "subject": result["subject"], "score": result["score"],
        "total": result["total"], "status": "PASSED" if score >= len(questions) / 2 else "NEEDS REVISION",
        "date": result["submitted_at"].isoformat(),
    }


@router.get("/assessments/results")
def assessment_results(connection: ConnectionDependency, token: TokenDependency) -> dict[str, list[dict[str, object]]]:
    rows = connection.execute(
        """
        SELECT a.id, u.student_number, a.subject, a.score, a.total, a.answers, a.submitted_at
        FROM assessments a JOIN users u ON u.id = a.learner_id
        WHERE a.school_id = %s AND (%s IN ('teacher', 'admin') OR a.learner_id = %s)
        ORDER BY a.submitted_at DESC
        """,
        (token["school_id"], token["role"], token["sub"]),
    ).fetchall()
    return {"assessments": [_serialize_assessment(row) for row in rows]}


def _require_staff(token: dict[str, int | str]) -> None:
    if token["role"] not in {"admin", "teacher"}:
        raise HTTPException(status_code=403, detail="Staff access required")


def _school_slug(connection: Connection, school_id: int) -> str:
    row = connection.execute("SELECT slug FROM schools WHERE id = %s", (school_id,)).fetchone()
    return row["slug"] if row else ""


def _new_reference_code(connection: Connection) -> str:
    return f"APP-{uuid4().hex[:10].upper()}"


def _serialize_application(row: dict[str, object]) -> dict[str, object]:
    created_at = row["created_at"]
    return {**row, "created_at": created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)}


def _serialize_assessment(row: dict[str, object]) -> dict[str, object]:
    submitted_at = row["submitted_at"]
    return {
        "id": row["id"], "student_number": row["student_number"], "subject": row["subject"],
        "score": row["score"], "total": row["total"],
        "status": "PASSED" if row["score"] >= row["total"] / 2 else "NEEDS REVISION",
        "date": submitted_at.isoformat() if isinstance(submitted_at, datetime) else str(submitted_at),
        "answers": row["answers"],
    }
