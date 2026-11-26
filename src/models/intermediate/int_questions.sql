{{ config(materialized='view') }}
 
SELECT
    question,
    category,
    difficulty,
    type,
    incorrect_answers,
    correct_answer,
    ai_answer,
    ai_correct,
    response_time,
    COALESCE(NULLIF(TRIM(ai_model), ''), 'google/gemma-3-4b') AS ai_model,
    source_file,
 
    CASE
        WHEN ai_answer IS NULL
          OR TRIM(ai_answer) = ''
        THEN TRUE
        ELSE FALSE
    END AS is_unanswered,
 
    CASE
        WHEN ai_correct = TRUE THEN 'Correcte'
        WHEN ai_correct = FALSE THEN 'Incorrecte'
        ELSE 'Non évaluée'
    END AS answer_status,
 
    CASE
        WHEN response_time IS NULL
          OR response_time < 0
        THEN NULL
        ELSE response_time
    END AS clean_response_time
 
FROM {{ ref('stg_questions') }}
 