"""
Enterprise-Grade Improvements for BFGMiner Application
"""

import datetime
import json
import logging
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import bcrypt
import psutil
from blockchain_validator import BlockchainValidator
from config import AppConfig
from dotenv import load_dotenv
from eth_account import Account
from flask import Flask, abort, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mnemonic import Mnemonic
from web3 import Web3
from web3.providers import HTTPProvider

# Configure enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bfgminer_enterprise.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

load_dotenv()


class SecurityManager:
    def __init__(self, config):
        self.config = config
        self.failed_attempts = {}

    def hash_password(self, password):
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(rounds=self.config.security.BCRYPT_ROUNDS),
        )

    def verify_password(self, password, hashed):
        return bcrypt.checkpw(password.encode("utf-8"), hashed)

    def record_failed_attempt(self, identifier):
        self.failed_attempts[identifier] = self.failed_attempts.get(identifier, 0) + 1

    def is_locked_out(self, identifier):
        attempts = self.failed_attempts.get(identifier, 0)
        return attempts >= self.config.security.MAX_LOGIN_ATTEMPTS

    def clear_failed_attempts(self, identifier):
        self.failed_attempts.pop(identifier, None)

    def generate_session_token(self):
        return secrets.token_hex(32)

    def validate_input(self, value, field_type):
        import re

        if field_type == "email":
            return bool(re.match(r"[^@]+@[^@]+\.[^@]+", value))
        elif field_type == "private_key":
            if value.startswith("0x"):
                value = value[2:]
            return len(value) == 64 and all(
                c in "0123456789abcdefABCDEF" for c in value
            )
        elif field_type == "wallet_address":
            if not value.startswith("0x") or len(value) != 42:
                return False
            return all(c in "0123456789abcdefABCDEF" for c in value[2:])
        return False


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            wallet_address TEXT UNIQUE NOT NULL,
            connection_type TEXT NOT NULL,
            is_validated BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_name TEXT NOT NULL,
            download_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            risk_level TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            source_ip TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
        )
        conn.commit()
        conn.close()

    from contextlib import contextmanager

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()


class AuditLogger:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def log_action(
        self,
        user_id,
        action,
        resource_type=None,
        resource_id=None,
        details=None,
        ip_address=None,
        risk_level=None,
    ):
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address, risk_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    action,
                    resource_type,
                    resource_id,
                    json.dumps(details or {}),
                    ip_address,
                    risk_level,
                ),
            )

    def log_security_event(self, event_type, severity, source_ip=None, details=None):
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO security_events (event_type, severity, source_ip, details) VALUES (?, ?, ?, ?)",
                (event_type, severity, source_ip, json.dumps(details or {})),
            )


class EnterpriseBlockchainValidator:
    def __init__(self, config):
        self.config = config
        self.w3 = None

    def connect_to_blockchain(self):
        for url in self.config.blockchain.ETHEREUM_RPC_URLS:
            try:
                self.w3 = Web3(Web3.HTTPProvider(url))
                if self.w3.is_connected():
                    return True
            except:
                continue
        return False

    def validate_mnemonic(self, mnemonic):
        try:
            mnemo = Mnemonic("english")
            if not mnemo.check(mnemonic):
                return {"valid": False, "message": "Invalid mnemonic"}

            # Derive wallet from mnemonic
            wallet_info = self.get_wallet_from_mnemonic(mnemonic)
            if not wallet_info:
                return {
                    "valid": False,
                    "message": "Failed to derive wallet from mnemonic",
                }

            # Get balance for validation
            balance_info = self.get_balance(wallet_info["address"])
            balance_usd = balance_info.get("balance_usd", 0) if balance_info else 0

            return {
                "valid": True,
                "message": "Valid BIP39 mnemonic",
                "address": wallet_info["address"],
                "balance_usd": balance_usd,
                "balance_eth": (
                    balance_info.get("balance_eth", 0) if balance_info else 0
                ),
            }
        except Exception as e:
            return {"valid": False, "message": f"Invalid mnemonic: {str(e)}"}

    def get_wallet_from_mnemonic(self, mnemonic):
        try:
            mnemo = Mnemonic("english")
            seed = mnemo.to_seed(mnemonic)
            account = Account.from_key(seed[:32])  # First 32 bytes for private key
            return {"address": account.address, "private_key": account.key.hex()}
        except:
            return None

    def get_balance(self, address, chain="ethereum"):
        if not self.w3:
            self.connect_to_blockchain()
        if not self.w3:
            return None
        try:
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, "ether")
            # Placeholder ETH price; in production, fetch from API
            eth_price = 2500.0
            balance_usd = float(balance_eth) * eth_price
            return {"balance_eth": float(balance_eth), "balance_usd": balance_usd}
        except Exception as e:
            logger.error(f"Balance fetch error: {e}")
            return None

    def validate_private_key(self, private_key):
        try:
            if private_key.startswith("0x"):
                private_key = private_key[2:]
            if len(private_key) != 64:
                return {"valid": False, "message": "Invalid length"}
            key = bytes.fromhex(private_key)
            account = Account.from_key(key)

            # Get balance for validation
            balance_info = self.get_balance(account.address)
            balance_usd = balance_info.get("balance_usd", 0) if balance_info else 0

            return {
                "valid": True,
                "message": "Valid",
                "address": account.address,
                "balance_usd": balance_usd,
                "balance_eth": (
                    balance_info.get("balance_eth", 0) if balance_info else 0
                ),
            }
        except Exception as e:
            return {"valid": False, "message": f"Invalid: {str(e)}"}
