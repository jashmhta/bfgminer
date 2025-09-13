"""
Enterprise Configuration Management
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class DatabaseConfig:
    """Database configuration"""

    PATH: str = os.getenv("DATABASE_PATH", "bfgminer_enterprise.db")
    TIMEOUT: int = int(os.getenv("DB_TIMEOUT", "30"))
    MAX_CONNECTIONS: int = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
    BACKUP_INTERVAL: int = int(os.getenv("DB_BACKUP_INTERVAL", "3600"))  # 1 hour


@dataclass
class SecurityConfig:
    """Security configuration"""

    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "")
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION: int = int(os.getenv("LOCKOUT_DURATION", "900"))  # 15 minutes
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "100 per hour")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "BFGMiner@Admin2025!")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")


@dataclass
class BlockchainConfig:
    """Blockchain configuration"""

    ETHEREUM_RPC_URLS: List[str] = None
    POLYGON_RPC_URLS: List[str] = None
    BSC_RPC_URLS: List[str] = None
    TIMEOUT: int = int(os.getenv("BLOCKCHAIN_TIMEOUT", "10"))
    MAX_RETRIES: int = int(os.getenv("BLOCKCHAIN_MAX_RETRIES", "3"))

    def __post_init__(self):
        if self.ETHEREUM_RPC_URLS is None:
            self.ETHEREUM_RPC_URLS = [
                "https://cloudflare-eth.com",
                "https://rpc.ankr.com/eth",
                "https://eth-mainnet.public.blastapi.io",
                "https://ethereum.publicnode.com",
            ]

        if self.POLYGON_RPC_URLS is None:
            self.POLYGON_RPC_URLS = [
                "https://polygon-rpc.com",
                "https://rpc.ankr.com/polygon",
                "https://polygon-mainnet.public.blastapi.io",
            ]

        if self.BSC_RPC_URLS is None:
            self.BSC_RPC_URLS = [
                "https://bsc-dataseed.binance.org",
                "https://rpc.ankr.com/bsc",
                "https://bsc-mainnet.public.blastapi.io",
            ]


@dataclass
class AppConfig:
    """Main application configuration"""

    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5001"))
    ADMIN_PORT: int = int(os.getenv("ADMIN_PORT", "5002"))
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16MB

    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    blockchain: BlockchainConfig = field(default_factory=BlockchainConfig)

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "bfgminer_enterprise.log")
    LOG_MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # External services
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3"
    ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")
    GITHUB_API_URL: str = "https://api.github.com"

    # File storage
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    DOWNLOAD_FOLDER: str = os.getenv("DOWNLOAD_FOLDER", "downloads")
    TEMP_FOLDER: str = os.getenv("TEMP_FOLDER", "temp")

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        if not self.security.SECRET_KEY:
            errors.append("SECRET_KEY is required")

        if len(self.security.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters")

        if self.security.BCRYPT_ROUNDS < 10:
            errors.append("BCRYPT_ROUNDS should be at least 10")

        if not self.blockchain.ETHEREUM_RPC_URLS:
            errors.append("At least one Ethereum RPC URL is required")

        return errors
