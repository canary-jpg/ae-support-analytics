with source as (
    select * from {{ source('support', 'customers') }}
),

renamed as (
    select
        customer_id,
        company_name,
        contact_name,
        email,
        plan,
        country,
        mrr,
        cast(created_at as timestamp) as created_at 
    from source
)

select * from renamed 