with source as (
    select * from {{ source('support', 'tickets') }}
),

renamed as (
    select 
        ticket_id,
        customer_id,
        agent_id,
        subject,
        category,
        priority,
        status,
        channel,
        cast(created_at as timestamp) as created_at,
        cast(first_response_at as timestamp) as first_response_at,
        cast(resolved_at as timestamp) as resolved_at,
        first_response_hours,
        resolution_hours,
        cast(sla_target_hours as int64) as sla_target_hours,
        sla_breached,
        is_escalated,
        csat_score,
        satisfaction_rating
    from source
)

select * from renamed 