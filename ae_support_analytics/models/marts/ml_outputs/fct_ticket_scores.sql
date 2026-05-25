with scores as (
    select * from `ae-project-portfolio.support_raw.ticket_ml_scores`
),

tickets as (
    select 
        ticket_id,
        customer_id,
        agent_id,
        category,
        priority,
        channel,
        status,
        is_escalated,
        sla_breached,
        sla_performance,
        csat_score,
        customer_plan,
        customer_mrr,
        agent_level,
        assigned_team,
        created_at 
    from {{ ref('fct_tickets') }}
),

final as (
    select 
        s.ticket_id,
        s.predicted_category,
        s.category_confidence,
        s.escalation_probability,
        s.escalation_prediction,
        s.escalation_risk_tier,
        s.scored_at,

        --ticket context
        t.customer_id,
        t.agent_id,
        t.category as actual_category,
        t.priority,
        t.channel,
        t.status,
        t.is_escalated as actual_escalated,
        t.sla_breached,
        t.sla_performance,
        t.csat_score,
        t.customer_plan,
        t.customer_mrr,
        t.agent_level,
        t.assigned_team,
        t.created_at,

        --was the category prediction correct?
        s.predicted_category = t.category as category_correct,

        --high value at risk flag
        case    
            when s.escalation_risk_tier in ('high', 'critical')
            and t.customer_mrr > 500 then true 
            else false 
        end as is_high_value_at_risk,

        --routing recommendation
        case 
            when s.predicted_category = 'billing' then 'billing'
            when s.predicted_category = 'bug' then 'bug'
            when s.predicted_category = 'performance' then 'technical'
            when s.predicted_category = 'integration' then 'technical'
            when s.predicted_category = 'feature_request' then 'general'
            else 'general'
        end as recommended_team
    from scores s 
    left join tickets t using (ticket_id)
 )

 select * from final 