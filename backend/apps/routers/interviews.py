from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.ai.llm_service import LLMService
from apps.core.dependencies import get_current_user
from apps.db.database import get_db
from apps.models.interview import Interview
from apps.models.question import Question
from apps.models.user import User
from apps.schemas.interview import (
    InterviewCreateRequest,
    InterviewListResponse,
    QuestionGenerateRequest,
    QuestionListResponse,
    QuestionResponse,
    InterviewResponse,
    InterviewStatusUpdateRequest,
)

router = APIRouter(prefix="/interviews", tags=["Interviews"])
llm_service = LLMService()


def _to_response(interview: Interview) -> InterviewResponse:
    return InterviewResponse(
        id=interview.id,
        user_id=interview.user_id,
        title=interview.title,
        role=interview.role,
        domain=interview.domain,
        mode=interview.mode,
        difficulty=interview.difficulty,
        status=interview.status,
        job_description=interview.job_description,
        started_at=interview.started_at,
        completed_at=interview.completed_at,
        created_at=interview.created_at,
        updated_at=interview.updated_at,
    )


@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(
    payload: InterviewCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewResponse:
    interview = Interview(
        user_id=current_user.id,
        title=payload.title.strip(),
        role=payload.role.strip(),
        domain=payload.domain.strip() if payload.domain else None,
        mode=payload.mode.strip() if payload.mode else None,
        difficulty=payload.difficulty.strip() if payload.difficulty else None,
        job_description=payload.job_description,
        status="created",
    )
    db.add(interview)
    await db.commit()
    await db.refresh(interview)
    return _to_response(interview)


@router.post("/{interview_id}/questions/generate", response_model=QuestionListResponse)
async def generate_interview_questions(
    interview_id: int,
    payload: QuestionGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionListResponse:
    interview = (
        await db.execute(
            select(Interview).where(
                Interview.id == interview_id,
                Interview.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    interview_context = (
        f"Role: {interview.role}\n"
        f"Domain: {interview.domain or 'general'}\n"
        f"Mode: {interview.mode or 'technical'}\n"
        f"Difficulty: {interview.difficulty or 'medium'}\n"
        f"Job Description: {interview.job_description or 'N/A'}\n"
    )

    try:
        generated = await llm_service.generate_questions(
            interview_context=interview_context,
            count=payload.count,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    await db.execute(delete(Question).where(Question.interview_id == interview.id))
    question_rows: list[Question] = []
    for index, item in enumerate(generated, start=1):
        question = Question(
            interview_id=interview.id,
            question_text=str(item.get("question_text", "")).strip() or f"Question {index}",
            question_type=(item.get("question_type") or "technical"),
            difficulty=(item.get("difficulty") or interview.difficulty or "medium"),
            order_index=index,
            category=item.get("category"),
            expected_answer=item.get("expected_answer"),
        )
        db.add(question)
        question_rows.append(question)

    if not question_rows:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM service did not return any questions.",
        )

    await db.commit()
    for question in question_rows:
        await db.refresh(question)

    return QuestionListResponse(
        items=[
            QuestionResponse(
                id=question.id,
                interview_id=question.interview_id,
                question_text=question.question_text,
                question_type=question.question_type,
                difficulty=question.difficulty,
                order_index=question.order_index,
                category=question.category,
                expected_answer=question.expected_answer,
            )
            for question in question_rows
        ]
    )


@router.get("", response_model=InterviewListResponse)
async def list_my_interviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewListResponse:
    stmt = (
        select(Interview)
        .where(Interview.user_id == current_user.id)
        .order_by(desc(Interview.created_at))
    )
    interviews = (await db.execute(stmt)).scalars().all()
    return InterviewListResponse(items=[_to_response(item) for item in interviews])


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewResponse:
    stmt = (
        select(Interview)
        .options(
            selectinload(Interview.questions),
            selectinload(Interview.answers),
        )
        .where(Interview.id == interview_id, Interview.user_id == current_user.id)
    )
    interview = (await db.execute(stmt)).scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    return _to_response(interview)


@router.patch("/{interview_id}/status", response_model=InterviewResponse)
async def update_interview_status(
    interview_id: int,
    payload: InterviewStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewResponse:
    interview = (
        await db.execute(
            select(Interview).where(
                Interview.id == interview_id,
                Interview.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

    interview.status = payload.status
    if payload.status == "in_progress" and interview.started_at is None:
        interview.started_at = datetime.now(timezone.utc)
    if payload.status == "completed":
        interview.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(interview)
    return _to_response(interview)
