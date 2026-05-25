with source as (
    select * from {{ source('support', 'ticket_comments') }}
),

renamed as (
    select 
        comment_id,
        ticket_id,
        author_type,
        body,
        cast(created_at as timestamp) as created_at 
    from source 
)

select * from renamed 