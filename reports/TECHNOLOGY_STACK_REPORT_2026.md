# Technology Stack Report 2026

Generated from the master company file on 2026-11-21. A stack is listed only when the source
record carries public evidence; `UNKNOWN` means no reliable evidence was captured.

## Search vocabulary

The collector searches 37 technologies (the `TECH` map in
`scripts/noida_it_collector.py`, including Go). Counts of companies whose captured stack contains
each term:

| Technology | Companies |
|---|---:|
| Java | 2 |
| Spring Boot | 0 |
| Python | 2 |
| JavaScript | 13 |
| TypeScript | 1 |
| React | 1 |
| Angular | 1 |
| Node.js | 1 |
| Django | 1 |
| FastAPI | 1 |
| .NET | 10 |
| C++ | 1 |
| Go | 0 |
| SQL | 2 |
| PostgreSQL | 0 |
| MongoDB | 0 |
| Redis | 0 |
| Spark | 1 |
| Kafka | 1 |
| Airflow | 1 |
| Snowflake | 0 |
| Databricks | 0 |
| PyTorch | 1 |
| TensorFlow | 1 |
| LangChain | 0 |
| LLM | 3 |
| RAG | 0 |
| MLOps | 1 |
| AWS | 3 |
| Azure | 2 |
| GCP | 1 |
| Docker | 1 |
| Kubernetes | 2 |
| Terraform | 2 |
| Jenkins | 1 |
| SAP | 2 |
| Salesforce | 2 |

## Confidence distribution

| Confidence | Companies |
|---|---:|
| PUBLICLY_REPORTED | 13 |
| UNKNOWN | 79 |

## Scoring note

`student_fit_score` uses word-boundary matching for AI signals (`ai`, `ml`, `llm`); substrings such as
"RateGain", "Retail" and "Airflow" do not produce an AI signal. Tests covering those cases live in
`tests/test_data.py`.
