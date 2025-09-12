"""
Enterprise-Grade Test Suite for BFGMiner Application
"""

import os
import sys
import tempfile
from unittest.mock import Mock, patch

import pytest

sys.path.append("..")

from enterprise_improvements import (AppConfig, AuditLogger, DatabaseManager, # noqa: E402
                                     EnterpriseBlockchainValidator,
                                     SecurityManager) # noqa: E402
from error_handler import (AuthenticationError, BFGMinerException, # noqa: E402
                           BlockchainError, ErrorCode, ValidationError) # noqa: E402
from monitoring import DatabaseMonitor, SystemMonitor # noqa: E402 # noqa: E402


class TestSecurityManager:
    """Test security management functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.config = AppConfig()
        self.security_manager = SecurityManager(self.config)

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = self.security_manager.hash_password(password)

        assert hashed != password
        assert self.security_manager.verify_password(password, hashed)
        assert not self.security_manager.verify_password("WrongPassword", hashed)

    def test_lockout_mechanism(self):
        """Test account lockout after failed attempts"""
        identifier = "test_user"

        # Should not be locked initially
        assert not self.security_manager.is_locked_out(identifier)

        # Record failed attempts
        for _ in range(self.config.MAX_LOGIN_ATTEMPTS):
            self.security_manager.record_failed_attempt(identifier)

        # Should be locked out now
        assert self.security_manager.is_locked_out(identifier)

        # Clear attempts should unlock
        self.security_manager.clear_failed_attempts(identifier)
        assert not self.security_manager.is_locked_out(identifier)

    def test_session_token_generation(self):
        """Test session token generation"""
        token1 = self.security_manager.generate_session_token()
        token2 = self.security_manager.generate_session_token()

        assert token1 != token2
        assert len(token1) >= 32
        assert len(token2) >= 32

    def test_input_validation(self):
        """Test input validation"""
        # Email validation
        assert self.security_manager.validate_input("test@example.com", "email")
        assert not self.security_manager.validate_input("invalid-email", "email")

        # Private key validation
        assert self.security_manager.validate_input("0x" + "a" * 64, "private_key")
        assert self.security_manager.validate_input("a" * 64, "private_key")
        assert not self.security_manager.validate_input("invalid", "private_key")

        # Wallet address validation
        assert self.security_manager.validate_input("0x" + "a" * 40, "wallet_address")
        assert not self.security_manager.validate_input(
            "0x" + "a" * 39, "wallet_address"
        )


class TestDatabaseManager:
    """Test database management functionality"""

    def setup_method(self):
        """Setup test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)

    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)

    def test_database_initialization(self):
        """Test database schema creation"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                "users",
                "sessions",
                "wallets",
                "downloads",
                "audit_logs",
                "security_events",
            ]
            for table in expected_tables:
                assert table in tables

    def test_connection_context_manager(self):
        """Test database connection context manager"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_transaction_rollback(self):
        """Test transaction rollback on error"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                    ("test@example.com", "hashed_password"),
                )
                # Force an error
                cursor.execute("INSERT INTO invalid_table (col) VALUES (?)", ("value",))
        except Exception:
            pass

        # Check that the first insert was rolled back
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE email = ?", ("test@example.com",)
            )
            count = cursor.fetchone()[0]
            assert count == 0


class TestAuditLogger:
    """Test audit logging functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.audit_logger = AuditLogger(self.db_manager)

    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)

    def test_log_action(self):
        """Test action logging"""
        self.audit_logger.log_action(
            user_id=1,
            action="WALLET_CONNECT",
            resource_type="wallet",
            resource_id="0x123...",
            details={"connection_type": "manual"},
            ip_address="192.168.1.1",
            risk_level="MEDIUM",
        )

        # Verify log was created
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audit_logs WHERE action = ?", ("WALLET_CONNECT",)
            )
            log = cursor.fetchone()

            assert log is not None
            assert log["user_id"] == 1
            assert log["action"] == "WALLET_CONNECT"
            assert log["risk_level"] == "MEDIUM"

    def test_log_security_event(self):
        """Test security event logging"""
        self.audit_logger.log_security_event(
            event_type="SUSPICIOUS_LOGIN",
            severity="HIGH",
            source_ip="192.168.1.100",
            details={"reason": "Multiple failed attempts"},
        )

        # Verify event was logged
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM security_events WHERE event_type = ?",
                ("SUSPICIOUS_LOGIN",),
            )
            event = cursor.fetchone()

            assert event is not None
            assert event["severity"] == "HIGH"
            assert event["source_ip"] == "192.168.1.100"


class TestBlockchainValidator:
    """Test blockchain validation functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.config = AppConfig()
        self.validator = EnterpriseBlockchainValidator(self.config)

    @patch("web3.Web3")
    def test_blockchain_connection(self, mock_web3):
        """Test blockchain connection with mocking"""
        mock_instance = Mock()
        mock_instance.is_connected.return_value = True
        mock_web3.return_value = mock_instance

        result = self.validator.connect_to_blockchain()
        assert result is True

    def test_private_key_validation_format(self):
        """Test private key format validation"""
        # Valid private key
        valid_key = "a" * 64
        result = self.validator.validate_private_key(valid_key)

        # Should validate format even if blockchain is not connected
        assert "valid" in result

        # Invalid private key
        invalid_key = "invalid"
        result = self.validator.validate_private_key(invalid_key)
        assert result["valid"] is False

    def test_mnemonic_validation_format(self):
        """Test mnemonic phrase format validation"""
        # Valid mnemonic (12 words)
        valid_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        result = self.validator.validate_mnemonic(valid_mnemonic)

        # Should validate format
        assert "valid" in result

        # Invalid mnemonic (wrong word count)
        invalid_mnemonic = "abandon abandon abandon"
        result = self.validator.validate_mnemonic(invalid_mnemonic)
        assert result["valid"] is False


class TestErrorHandling:
    """Test error handling functionality"""

    def test_bfgminer_exception(self):
        """Test custom exception creation"""
        error = BFGMinerException(
            message="Test error",
            error_code=ErrorCode.INVALID_INPUT,
            details={"field": "email"},
            http_status=400,
        )

        error_dict = error.to_dict()
        assert error_dict["success"] is False
        assert error_dict["error"]["code"] == ErrorCode.INVALID_INPUT
        assert error_dict["error"]["message"] == "Test error"
        assert error_dict["error"]["details"]["field"] == "email"

    def test_validation_error(self):
        """Test validation error"""
        error = ValidationError("Invalid email format", field="email", value="invalid")

        assert error.error_code == ErrorCode.INVALID_INPUT
        assert error.http_status == 400
        assert error.details["field"] == "email"
        assert error.details["value"] == "invalid"

    def test_authentication_error(self):
        """Test authentication error"""
        error = AuthenticationError("Invalid credentials")

        assert error.error_code == ErrorCode.INVALID_CREDENTIALS
        assert error.http_status == 401

    def test_blockchain_error(self):
        """Test blockchain error"""
        error = BlockchainError("Connection failed", blockchain="ethereum")

        assert error.error_code == ErrorCode.BLOCKCHAIN_CONNECTION_FAILED
        assert error.http_status == 503
        assert error.details["blockchain"] == "ethereum"


class TestMonitoring:
    """Test monitoring functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_monitor = DatabaseMonitor(self.temp_db.name)
        self.system_monitor = SystemMonitor()

    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)

    def test_system_metrics(self):
        """Test system metrics collection"""
        metrics = self.system_monitor.get_system_metrics()

        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "timestamp" in metrics

        assert "usage_percent" in metrics["cpu"]
        assert "total" in metrics["memory"]
        assert "free" in metrics["disk"]

    def test_database_health_check(self):
        """Test database health checking"""
        # Initialize database first
        DatabaseManager(self.temp_db.name)

        health = self.db_monitor.check_database_health()

        assert health.service == "database"
        assert health.status in ["healthy", "unhealthy"]
        assert health.response_time >= 0
        assert health.timestamp is not None


class TestIntegration:
    """Integration tests for complete workflows"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()

        self.config = AppConfig()
        self.config.database.PATH = self.temp_db.name

        self.db_manager = DatabaseManager(self.temp_db.name)
        self.security_manager = SecurityManager(self.config)
        self.audit_logger = AuditLogger(self.db_manager)

    def teardown_method(self):
        """Cleanup test database"""
        os.unlink(self.temp_db.name)

    def test_user_registration_workflow(self):
        """Test complete user registration workflow"""
        email = "test@example.com"
        password = "TestPassword123!"

        # Hash password
        password_hash = self.security_manager.hash_password(password)

        # Create user
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            user_id = cursor.lastrowid
            conn.commit()

        # Log registration
        self.audit_logger.log_action(
            user_id=user_id, action="USER_REGISTRATION", details={"email": email}
        )

        # Verify user was created
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()

            assert user is not None
            assert user["email"] == email
            assert self.security_manager.verify_password(
                password, user["password_hash"]
            )

        # Verify audit log
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audit_logs WHERE action = ?", ("USER_REGISTRATION",)
            )
            log = cursor.fetchone()

            assert log is not None
            assert log["user_id"] == user_id

    def test_wallet_connection_workflow(self):
        """Test complete wallet connection workflow"""
        # Create test user
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                ("test@example.com", "hashed_password"),
            )
            user_id = cursor.lastrowid
            conn.commit()

        # Connect wallet
        wallet_address = "0x742d35Cc6634C0532925a3b8D4C2b2e4C8b4b8b4"
        connection_type = "manual"

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO wallets
                   (user_id, wallet_address, connection_type, is_validated)
                   VALUES (?, ?, ?, ?)""",
                (user_id, wallet_address, connection_type, True),
            )
            wallet_id = cursor.lastrowid
            conn.commit()

        # Log wallet connection
        self.audit_logger.log_action(
            user_id=user_id,
            action="WALLET_CONNECT",
            resource_type="wallet",
            resource_id=str(wallet_id),
            details={
                "wallet_address": wallet_address,
                "connection_type": connection_type,
            },
        )

        # Verify wallet was connected
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM wallets WHERE id = ?", (wallet_id,))
            wallet = cursor.fetchone()

            assert wallet is not None
            assert wallet["wallet_address"] == wallet_address
            assert wallet["connection_type"] == connection_type
            assert wallet["is_validated"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
