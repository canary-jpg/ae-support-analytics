with source as (
    select * from {{ source('support', 'agent_team_history') }}
),

renamed as (
    select 
        history_id,
        agent_id,
        team,
        cast(effective_from as date) as effective_from,
        cast(effective_to as date) as effective_to,
        is_current
    from source 
)

select * from renamed