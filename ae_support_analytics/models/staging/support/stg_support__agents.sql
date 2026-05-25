with source as (
    select * from {{ source('support', 'agents') }}
),

renamed as (
    select 
        agent_id,
        first_name,
        last_name,
        email,
        team,
        level as agent_level,
        cast(hire_date as date) as hire_date,
        is_active,
        cast(created_at as timestamp) as created_at 
    from source 
)

select * from renamed 