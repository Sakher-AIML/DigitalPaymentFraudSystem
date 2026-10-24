USE digital_payment_fraud;
INSERT INTO customers(full_name,email,registration_date) VALUES
('Aarav Mehta','aarav@example.edu','2025-01-15'),('Diya Shah','diya@example.edu','2025-02-10'),
('Kabir Rao','kabir@example.edu','2025-03-03'),('Mira Iyer','mira@example.edu','2025-03-22')
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);
INSERT INTO accounts(customer_id,account_type,balance) SELECT c.customer_id,'WALLET',50000 FROM customers c WHERE c.email='aarav@example.edu' AND NOT EXISTS (SELECT 1 FROM accounts a WHERE a.customer_id=c.customer_id);
INSERT INTO accounts(customer_id,account_type,balance) SELECT c.customer_id,'SAVINGS',125000 FROM customers c WHERE c.email='diya@example.edu' AND NOT EXISTS (SELECT 1 FROM accounts a WHERE a.customer_id=c.customer_id);
INSERT INTO accounts(customer_id,account_type,balance) SELECT c.customer_id,'CURRENT',25000 FROM customers c WHERE c.email='kabir@example.edu' AND NOT EXISTS (SELECT 1 FROM accounts a WHERE a.customer_id=c.customer_id);
INSERT INTO accounts(customer_id,account_type,balance) SELECT c.customer_id,'WALLET',75000 FROM customers c WHERE c.email='mira@example.edu' AND NOT EXISTS (SELECT 1 FROM accounts a WHERE a.customer_id=c.customer_id);
INSERT INTO merchants(merchant_name,mcc) VALUES ('Campus Books','5942'),('Travel Desk','4722'),('Crypto Exchange Demo','6051'),('Grocery Hub','5411');
INSERT INTO transactions(source_account_id,merchant_id,amount,currency,transaction_type,channel,device_id,location,status,risk_score,risk_level)
SELECT a.account_id,m.merchant_id,1200,'INR','PURCHASE','MOBILE','seed-device-1','Pune','SETTLED',0,'LOW' FROM accounts a JOIN customers c ON c.customer_id=a.customer_id JOIN merchants m ON m.merchant_name='Campus Books' WHERE c.email='aarav@example.edu' LIMIT 1;
INSERT INTO transactions(source_account_id,merchant_id,amount,currency,transaction_type,channel,device_id,location,status,risk_score,risk_level)
SELECT a.account_id,m.merchant_id,72000,'INR','PURCHASE','WEB','seed-device-2','Mumbai','PENDING',45,'MEDIUM' FROM accounts a JOIN customers c ON c.customer_id=a.customer_id JOIN merchants m ON m.merchant_name='Crypto Exchange Demo' WHERE c.email='diya@example.edu' LIMIT 1;
