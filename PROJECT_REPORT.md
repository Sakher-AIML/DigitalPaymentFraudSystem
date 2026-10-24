# Digital Payment Transaction Monitoring & Fraud Risk Management System

## 1. Overview
This report documents a Streamlit academic application for monitoring fictional digital-payment activity and prioritizing potential fraud alerts.

## 2. Problem statement and objectives
Digital payment teams need joined customer, account, merchant, transaction, and investigation information. The project demonstrates safe storage, retrieval, explainable scoring, and analyst workflows.

## 3. Requirements and technology
Python 3.13-compatible code, Streamlit, MySQL 8, MongoDB, `mysql-connector-python`, `pymongo`, pandas, python-dotenv, and pytest.

## 4. Architecture
Streamlit calls modular Python services. MySQL owns financial records and procedures; MongoDB owns telemetry and audit history. Environment variables provide configuration.

## 5. Schema and relationships
Customers own accounts; accounts create transactions; merchants classify transactions. Risk rules connect to fraud alerts through `fraud_alert_rules`; alerts can have one investigation case.

## 6. Fraud methodology
Six deterministic rules evaluate velocity, amount, balance, device history, failed attempts, and MCC. Rule points are summed once, capped at 100, and mapped to configurable levels. A score indicates review priority, not guilt.

## 7. Implementation and pages
The six required pages provide dashboard KPIs, joined monitoring, simulated submissions, alert review, investigation cases, and health diagnostics.

## 8. Advanced operations
`sql/advanced_queries.sql` includes joins, grouping, aggregation, ordering, summaries, repeated-failure analysis, merchant risk, and case reporting. MongoDB indexes support event and audit retrieval.

## 9. Testing and validation
Database-independent pytest tests cover all rules, score caps, zero versus unevaluated scores, amount validation, case transitions, parameterized retrieval, and error propagation. Live integration results depend on local MySQL and MongoDB availability and should be recorded after running the setup check.

## 10. Results and limitations
No performance or live integration metrics are claimed here because they require the user's configured environment. The application intentionally uses fictional seed data and does not integrate with payment providers.

## 11. Conclusion and future scope
The project demonstrates an auditable baseline for payment risk monitoring. Future scope includes authentication, operational alert delivery, richer history, and governed model-assisted review.

## 12. References
Implementation references are the official documentation for Python, Streamlit, MySQL, MongoDB, pandas, and pytest. Exact URLs and accessed dates can be added for the final institutional submission.
