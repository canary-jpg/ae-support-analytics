"""
Support ticket synthetic data generator.
Produces realistic customer support data for a fictional SaaS company.
Writes directly to BigQuery raw tables
"""

import pandas as pd 
import numpy as np 
from faker import Faker 
from google.cloud import bigquery 
from datetime import datetime, timedelta 
import random
import uuid 

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

PROJECT = "ae-project-portfolio"
DATASET = "support_raw"
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)

client = bigquery.Client(project=PROJECT)

#helper functions
def random_data(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def write_to_bq(df, table_id, schema):
    full_table = f"{PROJECT}.{DATASET}.{table_id}"
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE"
    )
    job = client.load_table_from_dataframe(df, full_table, job_config=job_config)
    job.result()
    print(f"✓ Written {len(df):,} rows to {full_table}")

#agents
print("Generating agents...")

teams = ["billing", "technical", "general", "escalations"]
levels = ["junior", "mid", "senior"]
n_agents = 50

agents = []
for i in range(n_agents):
    hire_date = random_data(START_DATE - timedelta(days=730), END_DATE)
    agents.append({
        'agent_id': str(uuid.uuid4()),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'email': fake.email(),
        'team': random.choice(teams),
        'level': random.choices(levels, weights=[0.4, 0.4, 0.2])[0],
        'hire_date': hire_date.date().isoformat(),
        'is_active': random.random() > 0.1,
        'created_at': hire_date.isoformat()
    })

agents_df = pd.DataFrame(agents)

#agent team history (for SCD Type 2)
print("Generating agent team history...")

history = []
for agent in agents:
    #each agent has 1-3 team assignments over their career
    n_assignments = random.randint(1, 3)
    assignment_start = datetime.fromisoformat(agent['created_at'])

    for j in range(n_assignments):
        if j < n_assignments - 1:
            assignment_end = assignment_start + timedelta(days=random.randint(90, 365))
            is_current = False 
        else:
            assignment_end = None 
            is_current = True 
        
        history.append({
            'history_id': str(uuid.uuid4()),
            'agent_id': agent['agent_id'],
            'team': random.choice(teams),
            'effective_from': assignment_start.date().isoformat(),
            'effective_to': assignment_end.date().isoformat() if assignment_end else None,
            'is_current': is_current
        })

        if assignment_end:
            assignment_start = assignment_end 


history_df = pd.DataFrame(history)

#customers data
print("Generating customers...")

plans = ["free", "starter", "pro", "enterprise"]
n_customers = 5000

customers = []
for i in range(n_customers):
    created = random_data(START_DATE, END_DATE)
    customers.append({
        'customer_id': str(uuid.uuid4()),
        'company_name': fake.company(),
        'contact_name': fake.name(),
        'email': fake.email(),
        'plan': random.choices(plans, weights=[0.3, 0.3, 0.25, 0.15])[0],
        'country': fake.country_code(),
        'created_at': created.isoformat(),
        'mrr': round(random.uniform(0, 5000), 2)
    })

customers_df = pd.DataFrame(customers)

#tickets
print("Generating tickets...")

categories = ['billing', 'bug', 'feature_request', 'account', 'performance', 'integration']
priorities = ['low', 'normal', 'high', 'urgent']
statuses = ['open', 'pending', 'solved', 'closed']
channels = ['email', 'chat', 'phone', 'web']
n_tickets = 20000

#SLA targets by priority (hours)
sla_targets = {'low': 48, 'normal': 24, 'high': 8, 'urgent': 2}

tickets = []
for i in range(n_tickets):
    created = random_data(START_DATE, END_DATE)
    priority = random.choices(priorities, weights=[0.3, 0.4, 0.2, 0.1])[0]
    sla_hours = sla_targets[priority]
    agent = random.choice(agents)
    status = random.choices(statuses, weights=[0.1, 0.15, 0.5, 0.25])[0]
    customer = random.choice(customers)
    agent_level = agent['level']

    #first response time; varies by priority and agent level
    level_multiplier = {'junior': 1.4, 'mid': 1.0, 'senior': 0.7}.get(agent['level'], 1.0)
    first_response_hours = max(0.1, np.random.exponential(sla_hours * 0.3 * level_multiplier))
    first_response_at = created + timedelta(hours=first_response_hours)

    #resoltion time
    if status in ('solved', 'closed'):
        resolution_hours = max(first_response_hours,
                              np.random.exponential(sla_hours * level_multiplier))
        resolved_at = created + timedelta(hours=resolution_hours)
    else:
        resolution_hours = None 
        resolved_at = None 

    #SLA breach
    sla_breached = first_response_hours > sla_hours

    #escalation: more likely for urgent + unresolved + long resolution
    escalated = (priority == 'urgent' and random.random() > 0.6) or \
                (sla_breached and random.random() > 0.7)

    #CSAT: only for solved/closed
    if status in ('solved', 'closed'):
        #higher CSAT for senior agents, lower for breached SLA
        base_csat = 4.0 if not sla_breached else 3.0
        csat_score = round(min(5, max(1, np.random.normal(base_csat, 0.8))), 1)
    else:
        csat_score = None 

    tickets.append({
        'ticket_id': str(uuid.uuid4()),
        'customer_id': customer['customer_id'],
        'agent_id': agent['agent_id'],
        'subject': fake.sentence(nb_words=6),
        'category': random.choice(categories),
        'priority': priority,
        'status': status,
        'channel': random.choice(channels),
        'created_at': created.isoformat(),
        'first_response_at': first_response_at.isoformat(),
        'resolved_at': resolved_at.isoformat() if resolved_at else None,
        'first_response_hours': round(first_response_hours, 2),
        'resolution_hours': round(resolution_hours, 2) if resolution_hours else None,
        'sla_target_hours': int(sla_hours),
        'sla_breached': sla_breached,
        'is_escalated': escalated,
        'csat_score': csat_score,
        'satisfaction_rating': random.choice(['good', 'bad', 'neutral', None])
    })

tickets_df = pd.DataFrame(tickets)

#ticket comments
print("Generating ticket comments")

#realistic support comment templates by category
comment_templates = {
    'billing': [
        "I was charged twice for my subscription this month.",
        "My invoice shows incorrect amounts, please review.",
        "I need a refund for the duplicate payment.",
        "Can you explain the charges on my latest invoice?",
        "My payment failed but I was still charged.",
    ],
    'bug': [
        "The application crashes when I try to export data.",
        "I'm getting a 500 error on the dashboard page.",
        "The login button is not responding intermittently.",
        "Data is not syncing correctly between modules.",
        "The report generation feature is broken."
    ],
    'feature_request': [
         "It would be great to have bulk export functionality.",
         "Can you add dark mode to the dashboard?",
         "We need an API endpoint for custom integrations.",
         "Please add the ability to schedule automated reports.",
         "A mobile app would greatly import our workflow",
    ],
    'account': [
        "I need to update the billing email on my account.",
        "How do I add additional users to my team?",
        "I forgot my password and the reset email is not arriving.",
        "Can I transfer ownership of the account to a colleague.",
        "I need to downgrade my plan before the next billing cycle.",
    ],
    'performance': [
        "The dashboard is loading very slowly today.",
        "Queries are timing out on large datasets.",
        "The application has been down for the past 30 minutes.",
        "Export jobs are taking much longer than usual.",
        "We are experiencing significant latency on the API.",
    ],
    'integration': [
        "The Salesforce integration stopped syncing yesterday.",
        "We are having trouble connecting to you REST API.",
        "The webhook is not firing for certain events.",
        "Our Zapier integration is returning authentication errors.",
        "Can you help us set up SSO with our identity provider?",
    ]
}

comments = []
for ticket in tickets:
    n_comments = random.randint(1, 5)
    comment_time = datetime.fromisoformat(ticket['created_at'])
    category = ticket['category']

    for j in range(n_comments):
        comment_time = comment_time + timedelta(hours=random.uniform(0.5, 24))
        is_agent = j > 0 and random.random() > 0.4

        if is_agent:
            body = random.choice([
                "Thank you for contacting support. I'm looking into this now.",
                "I've escalated this to our technical team.",
                "Could you provide more details about the issue?",
                "This has been resolved. Please let me know if you need anything else.",
                "I've applied a fix on our end. Can you confirm the issue is resolved.",
            ])
        else:
            templates = comment_templates.get(category, comment_templates['bug'])
            body = random.choice(templates)

        comments.append({
            'comment_id': str(uuid.uuid4()),
            'ticket_id': ticket['ticket_id'],
            'author_type': 'agent' if is_agent else 'customer',
            'body': body,
            'created_at': comment_time.isoformat()
        })
comments_df = pd.DataFrame(comments)

#writing data to BigQuery
print("\nWriting to BigQuery...")

#create dataset if needed
try:
    client.create_dataset(f"{PROJECT}.{DATASET}", exists_ok=True)
    print(f"Dataset: {DATASET} is ready")
except Exception as e:
    print(f"Dataset note: {e}")

#print(tickets_df.dtypes)
#print(tickets_df.head(2))

write_to_bq(agents_df, 'agents', [
    bigquery.SchemaField("agent_id", "STRING"),
    bigquery.SchemaField("first_name", "STRING"),
    bigquery.SchemaField("last_name", "STRING"),
    bigquery.SchemaField("email", "STRING"),
    bigquery.SchemaField("team", "STRING"),
    bigquery.SchemaField("level", "STRING"),
    bigquery.SchemaField("hire_date", "STRING"),
    bigquery.SchemaField("is_active", "BOOLEAN"),
    bigquery.SchemaField("created_at", "STRING"),
])

write_to_bq(history_df, 'agent_team_history', [
    bigquery.SchemaField("history_id", "STRING"),
    bigquery.SchemaField("agent_id", "STRING"),
    bigquery.SchemaField("team", "STRING"),
    bigquery.SchemaField("effective_from", "STRING"),
    bigquery.SchemaField("effective_to", "STRING"),
    bigquery.SchemaField("is_current", "BOOLEAN"),
])

write_to_bq(customers_df, 'customers', [
    bigquery.SchemaField("customer_id", "STRING"),
    bigquery.SchemaField("company_name", "STRING"),
    bigquery.SchemaField("contact_name", "STRING"),
    bigquery.SchemaField("email", "STRING"),
    bigquery.SchemaField("plan", "STRING"),
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("created_at", "STRING"),
    bigquery.SchemaField("mrr", "FLOAT"),
])

tickets_df['sla_target_hours'] = tickets_df['sla_target_hours'].astype(float)
tickets_df['csat_score'] = pd.to_numeric(tickets_df['csat_score'], errors='coerce')
tickets_df['resolution_hours'] = pd.to_numeric(tickets_df['resolution_hours'], errors='coerce')
tickets_df['first_response_hours'] = pd.to_numeric(tickets_df['first_response_hours'], errors='coerce')

write_to_bq(tickets_df, 'tickets', [
    bigquery.SchemaField("ticket_id", "STRING"),
    bigquery.SchemaField("customer_id", "STRING"),
    bigquery.SchemaField("agent_id", "STRING"),
    bigquery.SchemaField("subject", "STRING"),
    bigquery.SchemaField("category", "STRING"),
    bigquery.SchemaField("priority", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("channel", "STRING"),
    bigquery.SchemaField("created_at", "STRING"),
    bigquery.SchemaField("first_response_at", "STRING"),
    bigquery.SchemaField("resolved_at", "STRING"),
    bigquery.SchemaField("first_response_hours", "FLOAT"),
    bigquery.SchemaField("resolution_hours", "FLOAT"),
    bigquery.SchemaField("sla_target_hours", "FLOAT"),
    bigquery.SchemaField("sla_breached", "BOOLEAN"),
    bigquery.SchemaField("is_escalated", "BOOLEAN"),
    bigquery.SchemaField("csat_score", "FLOAT"),
    bigquery.SchemaField("satisfaction_rating", "STRING"),
])

write_to_bq(comments_df, 'ticket_comments', [
    bigquery.SchemaField("comment_id", "STRING"),
    bigquery.SchemaField("ticket_id", "STRING"),
    bigquery.SchemaField("author_type", "STRING"),
    bigquery.SchemaField("body", "STRING"),
    bigquery.SchemaField("created_at", "STRING"),
])

print("\nAll tables written successfully!")
print(f" agents: {len(agents_df):,} rows")
print(f" agent_team_history: {len(history_df):,} rows")
print(f" customers: {len(customers_df):,} rows")
print(f" tickets: {len(tickets_df):,} rows")
print(f" ticket_comments: {len(comments_df):,} rows")
    