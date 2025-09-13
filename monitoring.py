"""
Enterprise Monitoring and Health Checks
"""

import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, List

import psutil
import requests


@dataclass
class HealthStatus:
    """Health check status"""

    service: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time: float
    details: Dict[str, Any]
    timestamp: datetime


class SystemMonitor:
    """System resource monitoring"""

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu": {"usage_percent": cpu_percent, "count": psutil.cpu_count()},
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100,
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now(UTC).isoformat()}


class DatabaseMonitor:
    """Database health monitoring"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def check_database_health(self) -> HealthStatus:
        """Check database connectivity and performance"""
        start_time = time.time()

        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                cursor = conn.cursor()

                # Test basic connectivity
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

                if result[0] != 1:
                    raise Exception("Database connectivity test failed")

                # Get database statistics
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM wallets")
                wallet_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM downloads")
                download_count = cursor.fetchone()[0]

                response_time = time.time() - start_time

                return HealthStatus(
                    service="database",
                    status="healthy",
                    response_time=response_time,
                    details={
                        "user_count": user_count,
                        "wallet_count": wallet_count,
                        "download_count": download_count,
                        "db_size": self._get_db_size(),
                    },
                    timestamp=datetime.now(UTC),
                )

        except Exception as e:
            response_time = time.time() - start_time
            return HealthStatus(
                service="database",
                status="unhealthy",
                response_time=response_time,
                details={"error": str(e)},
                timestamp=datetime.now(UTC),
            )

    def _get_db_size(self) -> int:
        """Get database file size in bytes"""
        try:
            import os

            return os.path.getsize(self.db_path)
        except OSError:
            return 0


class BlockchainMonitor:
    """Blockchain connectivity monitoring"""

    def __init__(self, rpc_urls: List[str]):
        self.rpc_urls = rpc_urls

    def check_blockchain_health(self) -> List[HealthStatus]:
        """Check all blockchain endpoints"""
        results = []

        for url in self.rpc_urls:
            start_time = time.time()

            try:
                # Test RPC connectivity
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1,
                }

                response = requests.post(
                    url,
                    json=payload,
                    timeout=10,
                    headers={"Content-Type": "application/json"},
                )

                response_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        block_number = int(data["result"], 16)

                        results.append(
                            HealthStatus(
                                service=f"blockchain_{url}",
                                status="healthy",
                                response_time=response_time,
                                details={"block_number": block_number, "endpoint": url},
                                timestamp=datetime.now(UTC),
                            )
                        )
                    else:
                        raise Exception(f"Invalid response: {data}")
                else:
                    raise Exception(f"HTTP {response.status_code}")

            except Exception as e:
                response_time = time.time() - start_time
                results.append(
                    HealthStatus(
                        service=f"blockchain_{url}",
                        status="unhealthy",
                        response_time=response_time,
                        details={"error": str(e), "endpoint": url},
                        timestamp=datetime.now(UTC),
                    )
                )

        return results


class ExternalServiceMonitor:
    """Monitor external service dependencies"""

    def check_coingecko_api(self) -> HealthStatus:
        """Check CoinGecko API health"""
        start_time = time.time()

        try:
            response = requests.get("https://api.coingecko.com/api/v3/ping", timeout=10)

            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return HealthStatus(
                    service="coingecko_api",
                    status="healthy",
                    response_time=response_time,
                    details=data,
                    timestamp=datetime.now(UTC),
                )
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            response_time = time.time() - start_time
            return HealthStatus(
                service="coingecko_api",
                status="unhealthy",
                response_time=response_time,
                details={"error": str(e)},
                timestamp=datetime.now(UTC),
            )

    def check_github_api(self) -> HealthStatus:
        """Check GitHub API health"""
        start_time = time.time()

        try:
            response = requests.get(
                "https://api.github.com/repos/luke-jr/bfgminer", timeout=10
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return HealthStatus(
                    service="github_api",
                    status="healthy",
                    response_time=response_time,
                    details={
                        "repo_name": data.get("name"),
                        "updated_at": data.get("updated_at"),
                        "size": data.get("size"),
                    },
                    timestamp=datetime.now(UTC),
                )
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            response_time = time.time() - start_time
            return HealthStatus(
                service="github_api",
                status="unhealthy",
                response_time=response_time,
                details={"error": str(e)},
                timestamp=datetime.now(UTC),
            )


class HealthChecker:
    """Comprehensive health checking"""

    def __init__(self, db_path: str, rpc_urls: List[str]):
        self.system_monitor = SystemMonitor()
        self.db_monitor = DatabaseMonitor(db_path)
        self.blockchain_monitor = BlockchainMonitor(rpc_urls)
        self.external_monitor = ExternalServiceMonitor()

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health_checks = []

        # System health
        system_metrics = self.system_monitor.get_system_metrics()

        # Database health
        db_health = self.db_monitor.check_database_health()
        health_checks.append(db_health)

        # Blockchain health
        blockchain_health = self.blockchain_monitor.check_blockchain_health()
        health_checks.extend(blockchain_health)

        # External services health
        coingecko_health = self.external_monitor.check_coingecko_api()
        github_health = self.external_monitor.check_github_api()
        health_checks.extend([coingecko_health, github_health])

        # Determine overall status
        unhealthy_services = [hc for hc in health_checks if hc.status == "unhealthy"]
        degraded_services = [hc for hc in health_checks if hc.status == "degraded"]

        if unhealthy_services:
            overall_status = "unhealthy"
        elif degraded_services:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "status": overall_status,
            "timestamp": datetime.now(UTC).isoformat(),
            "system_metrics": system_metrics,
            "services": {
                hc.service: {
                    "status": hc.status,
                    "response_time": hc.response_time,
                    "details": hc.details,
                    "timestamp": hc.timestamp.isoformat(),
                }
                for hc in health_checks
            },
            "summary": {
                "total_services": len(health_checks),
                "healthy_services": len(
                    [hc for hc in health_checks if hc.status == "healthy"]
                ),
                "degraded_services": len(degraded_services),
                "unhealthy_services": len(unhealthy_services),
            },
        }

    def get_readiness_status(self) -> Dict[str, Any]:
        """Get readiness status for load balancer"""
        db_health = self.db_monitor.check_database_health()

        # Service is ready if database is healthy
        is_ready = db_health.status == "healthy"

        return {
            "ready": is_ready,
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": {"database": db_health.status == "healthy"},
        }

    def get_liveness_status(self) -> Dict[str, Any]:
        """Get liveness status for container orchestration"""
        # Basic liveness check - service is alive if it can respond
        return {
            "alive": True,
            "timestamp": datetime.now(UTC).isoformat(),
            "uptime": time.time(),  # This would be actual uptime in production
        }
