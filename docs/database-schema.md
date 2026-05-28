# Database Schema

## Tables

### `users`

Stores registered platform users.

- `id`
- `username`
- `email`
- `password`
- `created_at`
- `updated_at`

### `interviews`

Stores each mock interview session.

- `id`
- `user_id`
- `title`
- `role`
- `domain`
- `mode`
- `difficulty`
- `status`
- `job_description`
- `started_at`
- `completed_at`
- `created_at`
- `updated_at`

### `interview_questions`

Stores generated AI interview questions.

- `id`
- `interview_id`
- `question_text`
- `question_type`
- `category`
- `difficulty`
- `order_index`
- `expected_answer`
- `created_at`

### `interview_answers`

Stores user answers and transcripts.

- `id`
- `interview_id`
- `question_id`
- `answer_text`
- `transcript`
- `audio_file_path`
- `duration_seconds`
- `created_at`

### `interview_feedback`

Stores AI evaluation for answers or full interviews.

- `id`
- `interview_id`
- `answer_id`
- `technical_score`
- `communication_score`
- `confidence_score`
- `problem_solving_score`
- `overall_score`
- `strengths`
- `weaknesses`
- `improvements`
- `summary`
- `created_at`

### `resumes`

Stores uploaded resume metadata and extracted text.

- `id`
- `user_id`
- `file_name`
- `file_path`
- `content_text`
- `ats_score`
- `created_at`
- `updated_at`

### `analytics`

Stores aggregated interview metrics for dashboards.

- `id`
- `user_id`
- `interview_id`
- `overall_score`
- `technical_score`
- `communication_score`
- `confidence_score`
- `problem_solving_score`
- `weak_topics`
- `strong_topics`
- `created_at`

### `embeddings_metadata`

Stores metadata for vectors saved in ChromaDB.

- `id`
- `user_id`
- `resume_id`
- `collection_name`
- `document_id`
- `source_type`
- `source_text`
- `created_at`

## Relationships

- One `user` has many `interviews`.
- One `user` has many `resumes`.
- One `interview` has many `interview_questions`.
- One `interview` has many `interview_answers`.
- One `interview` has many `interview_feedback` rows.
- One `answer` can have feedback.
- One `resume` can have many `embeddings_metadata` records.
