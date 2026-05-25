with agents as (
    select * from {{ ref('stg_support__agents') }}
),

history as (
    select * from {{ ref('stg_support__agent_team_history') }}
),

--SCD Type 2: join each eagent to their full team history
--each row represents one team assignment period
scd as (
    select 
        {{ dbt_utils.generate_surrogate_key(['h.history_id']) }} as agent_key,
        a.agent_id,
        a.first_name,
        a.last_name,
        a.email,
        a.agent_level,
        a.hire_date,
        a.is_active,
        h.team as assigned_team,
        h.effective_from,
        h.effective_to,
        h.is_current,

        --how long was this assignment?
        date_diff(
            coalesce(h.effective_to, current_date()),
            h.effective_from,
            day
        ) as days_in_role,

        --tenure at time of assignment start
        date_diff(
            h.effective_from,
            a.hire_date,
            day 
        ) as tenure_days_at_assignment
    from agents a 
    inner join history h using (agent_id)
)

select * from scd