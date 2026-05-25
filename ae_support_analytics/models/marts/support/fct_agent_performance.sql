with tickets as (
    select * from {{ ref('fct_tickets') }}
    where is_resolved = true 
),

weekly_stats as (
    select 
        agent_id,
        agent_first_name,
        agent_last_name,
        agent_level,
        assigned_team,
        ticket_week,

        count(ticket_id) as tickets_resolved,
        avg(first_response_hours) as avg_first_response_hours,
        avg(resolution_hours) as avg_resolution_hours,
        avg(csat_score) as avg_csat_score,
        countif(sla_breached) as sla_breaches,
        countif(is_escalated) as escalations,
        round(
            safe_divide(
                countif(sla_breached),
                count(ticket_id)
            ) * 100, 1
        ) as sla_breach_rate,
        round(
            safe_divide(
                countif(is_escalated),
                count(ticket_id)
            ) * 100, 1
        ) as escalation_rate
    from tickets
    group by 
        agent_id,
        agent_first_name,
        agent_last_name,
        agent_level,
        assigned_team,
        ticket_week 
)

select 
    {{ dbt_utils.generate_surrogate_key(['agent_id', 'ticket_week']) }} as performance_key,
    *
from weekly_stats