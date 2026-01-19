"""
Configuration module for IICS CI/CD Pipeline.
Centralizes all environment-specific settings.
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class IICSConfig:
    """Configuration for an IICS environment."""
    login_url: str
    pod_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    session_id: Optional[str] = None
    default_resource_type: str = "MTT"

    @classmethod
    def from_env(cls, prefix: str = "") -> "IICSConfig":
        """
        Create config from environment variables.
        
        Args:
            prefix: Optional prefix for env vars (e.g., "UAT_" for UAT environment)
        """
        return cls(
            login_url=os.environ.get("IICS_LOGIN_URL", "https://dm-em.informaticacloud.com"),
            pod_url=os.environ.get("IICS_POD_URL", ""),
            username=os.environ.get(f"{prefix}IICS_USERNAME"),
            password=os.environ.get(f"{prefix}IICS_PASSWORD"),
            session_id=os.environ.get(f"{prefix.lower()}sessionId"),
            default_resource_type=os.environ.get("RESOURCE_TYPE", "MTT"),
        )


# Pre-configured environment instances
def get_dev_config() -> IICSConfig:
    """Get Development environment configuration."""
    return IICSConfig.from_env()


def get_uat_config() -> IICSConfig:
    """Get UAT environment configuration."""
    return IICSConfig.from_env(prefix="UAT_")
