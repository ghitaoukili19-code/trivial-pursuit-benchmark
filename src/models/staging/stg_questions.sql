
{{ config(materialized='view') }}
 
SELECT *
FROM read_parquet('/home/goukili/projects/trivial-pursuit/silver/questions_clean.parquet')