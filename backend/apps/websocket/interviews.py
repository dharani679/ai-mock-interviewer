import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from apps.ai.llm_service import LLMService
from apps.core.security import decode_token
from apps.db.database import AsyncSessionLocal
from apps.models.answer import Answer
from apps.models.interview import Interview
from apps.models.question import Question
from apps.models.user import User

router = APIRouter(prefix="/ws/interviews", tags=["Interview WebSocket"])
llm_service = LLMService()
logger = logging.getLogger(__name__)


def _build_interview_context(interview: Interview) -> str:
    return (
        f"Role: {interview.role}\n"
        f"Domain: {interview.domain or 'general'}\n"
        f"Mode: {interview.mode or 'technical'}\n"
        f"Difficulty: {interview.difficulty or 'medium'}\n"
        f"Job Description: {interview.job_description or 'N/A'}\n"
    )


async def _authenticate_websocket(token: str | None) -> int | None:
    if not token:
        return None
    try:
        payload = decode_token(token)
    except ValueError:
        return None
    if payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    return int(user_id) if user_id else None


def _answer_text_from_message(message: str) -> str:
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        return message.strip()
    if payload.get("type") != "answer":
        return ""
    return str(payload.get("answer_text", "")).strip()


async def _send_question(websocket: WebSocket, question: Question) -> None:
    await websocket.send_json(
        {
            "type": "question",
            "question": {
                "id": question.id,
                "order_index": question.order_index,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "difficulty": question.difficulty,
                "category": question.category,
            },
        }
    )


@router.websocket("/{interview_id}")
async def interview_session(websocket: WebSocket, interview_id: int) -> None:
    await websocket.accept()
    logger.info("WebSocket accepted for interview_id=%s", interview_id)

    user_id = await _authenticate_websocket(websocket.query_params.get("token"))
    if user_id is None:
        logger.warning("WebSocket authentication failed for interview_id=%s", interview_id)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid access token")
        return

    async with AsyncSessionLocal() as db:
        logger.info("WebSocket authenticated user_id=%s interview_id=%s", user_id, interview_id)
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        interview = (
            await db.execute(
                select(Interview).where(
                    Interview.id == interview_id,
                    Interview.user_id == user_id,
                )
            )
        ).scalar_one_or_none()

        if user is None or interview is None:
            logger.warning("WebSocket interview lookup failed user_id=%s interview_id=%s", user_id, interview_id)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Interview not found")
            return

        interview.status = "in_progress"
        if interview.started_at is None:
            interview.started_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("Interview marked in_progress user_id=%s interview_id=%s", user_id, interview.id)

        questions = (
            await db.execute(
                select(Question)
                .where(Question.interview_id == interview.id)
                .order_by(Question.order_index.asc(), Question.id.asc())
            )
        ).scalars().all()

        if not questions:
            logger.info(
                "Generating questions user_id=%s interview_id=%s backend=%s",
                user_id,
                interview.id,
                llm_service.backend,
            )
            generated = await llm_service.generate_questions(
                interview_context=_build_interview_context(interview),
                count=5,
            )
            logger.info(
                "Generated questions user_id=%s interview_id=%s count=%s",
                user_id,
                interview.id,
                len(generated),
            )
            for index, item in enumerate(generated, start=1):
                question = Question(
                    interview_id=interview.id,
                    question_text=str(item.get("question_text", "")).strip() or f"Question {index}",
                    question_type=item.get("question_type") or "technical",
                    difficulty=item.get("difficulty") or interview.difficulty or "medium",
                    order_index=index,
                    category=item.get("category"),
                    expected_answer=item.get("expected_answer"),
                )
                db.add(question)
            await db.commit()
            logger.info("Saved generated questions user_id=%s interview_id=%s", user_id, interview.id)
            questions = (
                await db.execute(
                    select(Question)
                    .where(Question.interview_id == interview.id)
                    .order_by(Question.order_index.asc(), Question.id.asc())
                )
            ).scalars().all()

        answered_question_ids = set(
            (
                await db.execute(
                    select(Answer.question_id).where(
                        Answer.interview_id == interview.id,
                    )
                )
            ).scalars().all()
        )
        pending_questions = [question for question in questions if question.id not in answered_question_ids]
        logger.info(
            "WebSocket session started user_id=%s interview_id=%s total_questions=%s pending_questions=%s",
            user_id,
            interview.id,
            len(questions),
            len(pending_questions),
        )

        await websocket.send_json(
            {
                "type": "session_started",
                "interview_id": interview.id,
                "total_questions": len(questions),
                "remaining_questions": len(pending_questions),
            }
        )

        try:
            for question in pending_questions:
                logger.info(
                    "Sending question user_id=%s interview_id=%s question_id=%s order_index=%s",
                    user_id,
                    interview.id,
                    question.id,
                    question.order_index,
                )
                await _send_question(websocket, question)
                while True:
                    answer_text = _answer_text_from_message(await websocket.receive_text())
                    if answer_text:
                        break
                    logger.warning(
                        "Invalid WebSocket answer payload user_id=%s interview_id=%s question_id=%s",
                        user_id,
                        interview.id,
                        question.id,
                    )
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Send an answer as plain text or {'type':'answer','answer_text':'...'}",
                        }
                    )

                db.add(
                    Answer(
                        interview_id=interview.id,
                        question_id=question.id,
                        answer_text=answer_text,
                        transcript=answer_text,
                    )
                )
                await db.commit()
                logger.info(
                    "Saved answer user_id=%s interview_id=%s question_id=%s answer_length=%s",
                    user_id,
                    interview.id,
                    question.id,
                    len(answer_text),
                )
                logger.info(
                    "Answer evaluation skipped user_id=%s interview_id=%s question_id=%s reason=not_implemented",
                    user_id,
                    interview.id,
                    question.id,
                )
                await websocket.send_json(
                    {
                        "type": "answer_saved",
                        "question_id": question.id,
                    }
                )

            interview.status = "completed"
            interview.completed_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info("Interview completed user_id=%s interview_id=%s", user_id, interview.id)
            await websocket.send_json(
                {
                    "type": "completed",
                    "interview_id": interview.id,
                    "message": "Interview completed.",
                }
            )
            await websocket.close()
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected user_id=%s interview_id=%s", user_id, interview.id)
            return
        except Exception:
            logger.exception("WebSocket session failed user_id=%s interview_id=%s", user_id, interview.id)
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Interview session failed")
            return
