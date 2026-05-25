with tickets as (
    select * from {{ ref('stg_support__tickets') }}
),

agents as (
    select
        agent_id,
        first_name,
        last_name,
        agent_level,
        assigned_team
    from {{ ref('dim_agents') }}
    where is_current = true
),

customers as (
    select
        customer_id,
        company_name,
        plan,
        country,
        mrr
    from {{ ref('stg_support__customers') }}
),

final as (
    select
        t.ticket_id,
        t.customer_id,
        t.agent_id,
        t.subject,
        t.category,
        t.priority,
        t.status,
        t.channel,
        t.created_at,
        t.first_response_at,
        t.resolved_at,
        t.first_response_hours,
        t.resolution_hours,
        t.sla_target_hours,
        t.sla_breached,
        t.is_escalated,
        t.csat_score,
        t.satisfaction_rating,

        -- agent context
        a.first_name                            as agent_first_name,
        a.last_name                             as agent_last_name,
        a.agent_level,
        a.assigned_team,

        -- customer context
        c.company_name,
        c.plan                                  as customer_plan,
        c.country                               as customer_country,
        c.mrr                                   as customer_mrr,

        -- derived
        date(t.created_at)                      as ticket_date,
        extract(year from t.created_at)         as ticket_year,
        extract(month from t.created_at)        as ticket_month,
        format_date('%Y-%W', date(t.created_at)) as ticket_week,

        case
            when t.status in ('solved', 'closed') then true
            else false
        end                                     as is_resolved,

        -- SLA performance bucket
        case
            when not t.sla_breached             then 'within_sla'
            when t.first_response_hours <= t.sla_target_hours * 1.5
                                                then 'slightly_breached'
            else                                    'severely_breached'
        end                                     as sla_performance,

        -- response speed relative to SLA
        round(
            safe_divide(t.first_response_hours, t.sla_target_hours) * 100,
            1
        )                                       as sla_usage_pct

    from tickets t
    left join agents a using (agent_id)
    left join customers c using (customer_id)
)

select * from final