{{ config(materialized='table') }}
 
SELECT
    ai_model,
    category,
    difficulty,
    type,
    question,
    correct_answer,
    incorrect_answers,
    ai_answer,
    ai_correct,
    answer_status,
    is_unanswered,
    clean_response_time AS response_time,
    source_file
 
FROM {{ ref('int_questions') }}