# Support Analytics Engineering Portfolio - Project 2

An end-to-end analytics engineering project built on synthetic customer support data for a fictional SaaS company. Demonstrates SCD Type 2 modeling, SLA analytics, NLP ticket classification, and escalation prediction.

## Architecture

```
Synthetic Data (Python generator) → Staging Layer (dbt views) - cleaned, typed, renamed → Marts Layers (dbt tables) - SLA metrics, agent KPIs, customer health → Analysis Notebooks (Python) - SLA analysis, agent performance → ML Models (sklear + XGBoost) - NLP category classifier, escalation prediction → ML Output (dbt table) - predictions surfaced alongside ticket context
```

## Project Structure

```
ae-support-analytics/
├── data_generator/
│   └── generate_support_data.py   # synthetic data generation
├── analysis/
│   ├── 01_sla_analysis.ipynb
│   └── 02_agent_performance.ipynb
├── ml/
│   ├── 01_ticket_classifier.ipynb
│   └── models/                    # saved model artifacts
└── ae_support_analytics/          # dbt project
    ├── models/
    │   ├── staging/support/       # 5 staging models
    │   └── marts/
    │       ├── support/           # dim_agents, fct_tickets, 
    │       │                      # fct_agent_performance, fct_customer_health
    │       └── ml_outputs/        # fct_ticket_scores
    ├── macros/
    │   └── generate_schema_name.sql
    └── tests/
```

## Data Models

| Model | Layer | Rows | Description |
|---|---|---|---|
| `stg_support__agents` | Staging | 50 | Cleaned agents |
| `stg_support__agent_team_history` | Staging | 92 | Team assignment history |
| `stg_support__customers` | Staging | 5k | Cleaned customers |
| `stg_support__tickets` | Staging | 20k | Cleaned tickets |
| `stg_support__ticket_comments` | Staging | 60k | Cleaned comments |
| `dim_agents` | Marts | 92 | SCD Type 2 agent dimension |
| `fct_tickets` | Marts | 20k | Ticket lifecycle + SLA metrics |
| `fct_agent_performance` | Marts | 6.7k | Weekly agent KPIs |
| `fct_customer_health` | Marts | 5k | Customer health signals |
| `fct_ticket_scores` | ML Outputs | 20k | NLP + escalation predictions |

## Testing

57 total tests across sources, staging, and marts.

```bash
dbt build # runs all models & tests in dependency order
```

| Result | Count |
|---|---|
| Pass | 57 |
| Warn | 0 |
| Error | | 0 |

## Key Modeling Decisions

**SCD Type 2 on `dim_agents`:** Agents change teams over time. Using SCD Type 2 on the team history table means ticket-level reporting correctly reflects which team an agent was on *at the time* the ticket was created, not just their current team.

**Custom schema macro:** dbt's default behavior appends the custom schema name to the target schema (e.g. `dbt_support_dev_staging`). A `generate_schema_name` macro overrides this to use clean schema names (`staging`, `marts`); better for a shared warehouse environment.

**Singular test for `author_type`:** The `accepted_values` generic test caused a column name truncation issue in dbt 1.11. A singular test in `tests/` is more explicit and avoids the issue entirely.

## Analysis Highlights

**SLA Analysis:**
- SLA breach has a statistically significant negative impact on CSAT (t-test p < 0.05)
- Billing team has the highest breach rate, driven by disput complexity
- Urgent tickets breach SLA most frequently despite shortest targets

**Agent Performance:**
- Senior agents have 8.6% lower breach rate than junior agents
- CSAT gap between levels is small (+0.08) - breach rate is the bigger lever
- Escalatations team has highest CSAT, suggesting expectation-resetting works

## ML Models

**Category Classifier (TF-IDF + Logistic Regression)**
- Predicts ticket category from first customer comment text
- Used for auto-routing recommendations in `fct_ticket_scores`

**Escalation Prediction (XGBoost)**
- ROC-AUC: 0.96
- Recall on escalations: 0.99; catches nearly every real escalation
- Combines TF-IDF text features with structured features
- Optimized for recall over precision; missing an escalation is costlier than a false positive

## Setup

```bash
#1. generate synthetic data
pip install faker pandas numpy google-cloud-bigquery
python data_generator/generate_support_data.py

#2.authenticate
gcloud auth application-default login

#3.install dbt dependencies
cd ae_support_analytics
dbt deps

#4.run full pipeline
dbt build

#5.run notebooks
pip install scikit-learn xgboost matplotlib seaborn
jupyter notebook
```

## Stack

- **Warehouse:** Google BigQuery
- **Transformation:** dbt Core 1.11
- **Languages:** SQL, Python
- **ML:** scikit-learn, XGBoost
- **Visualization:** matplotlib, seaborn