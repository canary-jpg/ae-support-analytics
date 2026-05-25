with tickets as (
    select * from {{ ref('fct_tickets') }}
),

customers as (
    select * from {{ ref('stg_support__customers') }}
),

ticket_stats as (
    select 
        customer_id,
        count(ticket_id) as total_tickets,
        countif(is_resolved) as resolved_tickets,
        countif(is_escalated) as escalated_tickets,
        count(sla_breached) as sla_breached_tickets,
        avg(csat_score) as avg_csat,
        avg(resolution_hours) as avg_resolution_hours,
        min(created_at) as first_ticket_at,
        max(created_at) as last_ticket_at,
        countif(priority = 'urgent') as urgent_tickets,

        --repeat contact rate: multiple tickets on same day
        count(distinct date(created_at)) as days_with_tickets,

        --most common category
        array_agg(
            category order by created_at desc limit 1
        )[offset(0)] as latest_category,

        --last CSAT
        array_agg(
            csat_score ignore nulls
            order by created_at desc limit 1
        )[offset(0)] as latest_csat
    from tickets 
    group by customer_id 
),

final as (
    select 
        c.customer_id,
        c.company_name,
        c.plan,
        c.country,
        c.mrr,
        c.created_at as customer_since,

        --ticket metrics
        coalesce(t.total_tickets, 0) as total_tickets,
        coalesce(t.resolved_tickets, 0) as resolved_tickets,
        coalesce(t.escalated_tickets, 0) as escalated_tickets,
        coalesce(t.sla_breached_tickets, 0) as sla_breached_tickets,
        coalesce(t.urgent_tickets, 0) as urgent_tickets,
        t.avg_csat,
        t.avg_resolution_hours,
        t.first_ticket_at,
        t.last_ticket_at,
        t.latest_csat,
        t.days_with_tickets,

        --derived health signals
        round(
            safe_divide(t.escalated_tickets, t.total_tickets) * 100,
            1
        ) as escalation_rate,

        round(
            safe_divide(t.sla_breached_tickets, t.total_tickets) * 100,
            1
        ) as sla_breach_rate,

        --contact frequency
        round(
            safe_divide(
                t.total_tickets,
                date_diff(
                    current_date(),
                    date(c.created_at),
                    month
                )
            ), 2
        ) as tickets_per_month,

        --health score tier
        case 
            when t.escalated_tickets > 2
                or t.avg_csat < 2.5 then 'at_risk'
            when t.escalated_tickets > 0
                or t.avg_csat < 3.5 then 'needs_attention'
            when t.total_tickets = 0 then 'no_contact'
            else 'healthy'
        end as health_tier
    from customers c 
    left join ticket_stats t using (customer_id)
)

select * from final 