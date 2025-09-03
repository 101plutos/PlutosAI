{{ config(
    materialized='table',
    partition_by={
      "field": "transaction_date",
      "data_type": "date",
      "granularity": "month"
    }
) }}

select
    transaction_id,
    client_id,
    amount,
    currency,
    transaction_date,
    status
from {{ ref('silver_transactions') }}