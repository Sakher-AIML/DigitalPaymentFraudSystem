USE digital_payment_fraud;
-- Joined transaction/customer/merchant report.
SELECT t.transaction_id,c.full_name,a.account_id,m.merchant_name,t.amount,t.risk_level
FROM transactions t JOIN accounts a ON a.account_id=t.source_account_id
JOIN customers c ON c.customer_id=a.customer_id LEFT JOIN merchants m ON m.merchant_id=t.merchant_id
WHERE t.transaction_timestamp >= %s ORDER BY t.amount DESC LIMIT %s;
-- Aggregate risk summary.
SELECT risk_level,COUNT(*) transaction_count,COALESCE(SUM(amount),0) total_value,AVG(risk_score) average_score
FROM transactions GROUP BY risk_level ORDER BY total_value DESC;
-- Alert severity by day.
SELECT DATE(created_at) alert_day,severity,COUNT(*) alert_count FROM fraud_alerts
GROUP BY DATE(created_at),severity ORDER BY alert_day DESC,severity;
-- Customer transaction summary.
SELECT c.customer_id,c.full_name,COUNT(t.transaction_id) transaction_count,
SUM(t.amount) total_value,MAX(t.amount) maximum_amount
FROM customers c JOIN accounts a ON a.customer_id=c.customer_id
LEFT JOIN transactions t ON t.source_account_id=a.account_id GROUP BY c.customer_id,c.full_name;
-- Repeated failed attempts.
SELECT account_id,device_id,COUNT(*) failed_attempts,MAX(attempt_timestamp) latest_attempt
FROM payment_attempts WHERE result='FAILED' GROUP BY account_id,device_id HAVING COUNT(*) >= %s;
-- Merchant-level risk.
SELECT m.merchant_name,m.mcc,COUNT(t.transaction_id) transactions,
AVG(t.risk_score) average_risk,SUM(t.risk_level IN ('HIGH','CRITICAL')) flagged
FROM merchants m LEFT JOIN transactions t ON t.merchant_id=m.merchant_id
GROUP BY m.merchant_id,m.merchant_name,m.mcc ORDER BY flagged DESC;
-- Investigation reporting.
SELECT ic.case_id,ic.status,ic.assigned_investigator,fa.severity,fa.score,fa.created_at
FROM investigation_cases ic JOIN fraud_alerts fa ON fa.alert_id=ic.alert_id
WHERE ic.status <> %s ORDER BY ic.updated_at DESC;
