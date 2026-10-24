CREATE DATABASE IF NOT EXISTS digital_payment_fraud;
USE digital_payment_fraud;

CREATE TABLE IF NOT EXISTS customers (
  customer_id INT PRIMARY KEY AUTO_INCREMENT, full_name VARCHAR(120) NOT NULL,
  email VARCHAR(180) NOT NULL UNIQUE, registration_date DATE NOT NULL,
  status ENUM('ACTIVE','SUSPENDED','CLOSED') NOT NULL DEFAULT 'ACTIVE'
);
CREATE TABLE IF NOT EXISTS accounts (
  account_id INT PRIMARY KEY AUTO_INCREMENT, customer_id INT NOT NULL,
  account_type ENUM('SAVINGS','CURRENT','WALLET') NOT NULL, balance DECIMAL(14,2) NOT NULL DEFAULT 0,
  status ENUM('ACTIVE','BLOCKED','CLOSED') NOT NULL DEFAULT 'ACTIVE',
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id), CHECK (balance >= 0)
);
CREATE TABLE IF NOT EXISTS merchants (
  merchant_id INT PRIMARY KEY AUTO_INCREMENT, merchant_name VARCHAR(150) NOT NULL,
  mcc VARCHAR(10) NOT NULL, status ENUM('ACTIVE','SUSPENDED') NOT NULL DEFAULT 'ACTIVE'
);
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id BIGINT PRIMARY KEY AUTO_INCREMENT, source_account_id INT NOT NULL,
  destination_account_id INT NULL, merchant_id INT NULL, amount DECIMAL(14,2) NOT NULL,
  currency CHAR(3) NOT NULL DEFAULT 'INR', transaction_type VARCHAR(30) NOT NULL,
  channel VARCHAR(20) NOT NULL, device_id VARCHAR(100) NOT NULL, location VARCHAR(150),
  transaction_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('PENDING','SETTLED','DECLINED','REVERSED') NOT NULL DEFAULT 'PENDING',
  risk_score INT NULL, risk_level ENUM('LOW','MEDIUM','HIGH','CRITICAL','UNEVALUATED') NULL,
  UNIQUE KEY uq_transaction_submission (source_account_id, device_id, amount, transaction_timestamp),
  INDEX ix_transactions_risk (risk_level, transaction_timestamp),
  FOREIGN KEY (source_account_id) REFERENCES accounts(account_id),
  FOREIGN KEY (destination_account_id) REFERENCES accounts(account_id),
  FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id), CHECK (amount > 0),
  CHECK (risk_score IS NULL OR (risk_score BETWEEN 0 AND 100))
);
CREATE TABLE IF NOT EXISTS payment_attempts (
  attempt_id BIGINT PRIMARY KEY AUTO_INCREMENT, account_id INT NOT NULL,
  customer_id INT NOT NULL, attempt_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  result ENUM('SUCCESS','FAILED') NOT NULL, device_id VARCHAR(100) NOT NULL,
  failure_reason VARCHAR(255), FOREIGN KEY (account_id) REFERENCES accounts(account_id),
  FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS risk_rules (
  rule_id INT PRIMARY KEY AUTO_INCREMENT, rule_code VARCHAR(20) NOT NULL UNIQUE,
  description VARCHAR(255) NOT NULL, points INT NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS fraud_alerts (
  alert_id BIGINT PRIMARY KEY AUTO_INCREMENT, transaction_id BIGINT NOT NULL UNIQUE,
  score INT NOT NULL, severity VARCHAR(15) NOT NULL, status ENUM('OPEN','ACKNOWLEDGED','RESOLVED','FALSE_POSITIVE') NOT NULL DEFAULT 'OPEN',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, explanation TEXT NOT NULL,
  FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);
CREATE TABLE IF NOT EXISTS fraud_alert_rules (
  alert_id BIGINT NOT NULL, rule_id INT NOT NULL, PRIMARY KEY (alert_id, rule_id),
  FOREIGN KEY (alert_id) REFERENCES fraud_alerts(alert_id) ON DELETE CASCADE,
  FOREIGN KEY (rule_id) REFERENCES risk_rules(rule_id)
);
CREATE TABLE IF NOT EXISTS investigation_cases (
  case_id BIGINT PRIMARY KEY AUTO_INCREMENT, alert_id BIGINT NOT NULL UNIQUE,
  assigned_investigator VARCHAR(120) NOT NULL, status ENUM('OPEN','IN_REVIEW','CLOSED') NOT NULL DEFAULT 'OPEN',
  notes TEXT, resolution TEXT, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (alert_id) REFERENCES fraud_alerts(alert_id)
);

INSERT INTO risk_rules (rule_code, description, points) VALUES
('R-VEL-01','Excessive transaction velocity within the configured window',20),
('R-AMT-01','Transaction amount exceeds the configured threshold',25),
('R-BAL-01','Insufficient funds or balance inconsistency',35),
('R-DEV-01','Unusual device compared with account history',15),
('R-REP-01','Repeated failed payment attempts',20),
('R-MCC-01','Merchant category is configured as high risk',20)
ON DUPLICATE KEY UPDATE description=VALUES(description), points=VALUES(points);

DROP PROCEDURE IF EXISTS sp_settle_transaction;
DELIMITER //
CREATE PROCEDURE sp_settle_transaction(IN p_transaction_id BIGINT)
BEGIN
  DECLARE v_account INT; DECLARE v_amount DECIMAL(14,2); DECLARE v_balance DECIMAL(14,2); DECLARE v_status VARCHAR(20);
  START TRANSACTION;
  SELECT source_account_id, amount, status INTO v_account, v_amount, v_status FROM transactions WHERE transaction_id=p_transaction_id FOR UPDATE;
  IF v_status IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Transaction not found';
  ELSEIF v_status <> 'PENDING' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Transaction already processed';
  END IF;
  SELECT balance INTO v_balance FROM accounts WHERE account_id=v_account FOR UPDATE;
  IF v_balance < v_amount THEN UPDATE transactions SET status='DECLINED' WHERE transaction_id=p_transaction_id; SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Insufficient balance';
  ELSE UPDATE accounts SET balance=balance-v_amount WHERE account_id=v_account;
       UPDATE transactions SET status='SETTLED' WHERE transaction_id=p_transaction_id;
  END IF;
  COMMIT;
END//
CREATE PROCEDURE sp_create_investigation_case(IN p_alert_id BIGINT, IN p_investigator VARCHAR(120), IN p_notes TEXT, OUT p_case_id BIGINT)
BEGIN
  IF NOT EXISTS (SELECT 1 FROM fraud_alerts WHERE alert_id=p_alert_id) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Alert not found'; END IF;
  INSERT INTO investigation_cases(alert_id,assigned_investigator,notes) VALUES(p_alert_id,p_investigator,p_notes);
  SET p_case_id=LAST_INSERT_ID();
END//
CREATE PROCEDURE sp_resolve_investigation_case(IN p_case_id BIGINT, IN p_status VARCHAR(20), IN p_resolution TEXT, IN p_notes TEXT)
BEGIN
  IF p_status NOT IN ('OPEN','IN_REVIEW','CLOSED') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Invalid case status'; END IF;
  UPDATE investigation_cases SET status=p_status,resolution=p_resolution,notes=p_notes WHERE case_id=p_case_id;
  IF ROW_COUNT()=0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Case not found'; END IF;
END//
DELIMITER ;
