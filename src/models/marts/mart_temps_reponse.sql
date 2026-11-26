{{ config(materialized='table') }}
 
SELECT
    ai_model,
 
    COUNT(clean_response_time) AS measured_responses,
 
    ROUND(AVG(clean_response_time), 2)
        AS avg_response_time,
 
    ROUND(MIN(clean_response_time), 2)
        AS min_response_time,
 
    ROUND(MAX(clean_response_time), 2)
        AS max_response_time,
 
    ROUND(
        MEDIAN(clean_response_time),
        2
    ) AS median_response_time
 
FROM {{ ref('int_questions') }}
 
GROUP BY ai_model
 
 