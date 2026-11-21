# Technology Stack Report 2026

Generated from the master company file on 2026-11-20. A stack is listed only when the source
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

`student_fit_score` is the sum of five v2 components: AI/ML/Data/Python relevance 30,
Java/Python backend relevance 20, verified entry-level or internship opening 25, off-campus direct
application 15, and presence of stack evidence 10. Component hits in this build:

| Component | Weight | Companies matching |
|---|---:|---:|
| ai_data_python | 30 | 10 |
| java_python_backend | 20 | 4 |
| verified_entry_level | 25 | 0 |
| offcampus_direct_apply | 15 | 0 |
| stack_evidence | 10 | 13 |

No live job posting was verifiable, so the 25-point opening component is 0 for every row; no direct
application URL was available, so the 15-point component is also 0. Word-boundary matching prevents
"RateGain", "Retail" and "Airflow" from producing an AI signal. Tests live in `tests/test_data.py`.
