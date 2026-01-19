"""
Custom exceptions for IICS CI/CD Pipeline.
Provides specific error types for better error handling and debugging.
"""


class IICSError(Exception):
    """Base exception for all IICS-related errors."""
    pass


class IICSAuthenticationError(IICSError):
    """Raised when authentication to IICS fails."""
    pass


class IICSJobError(IICSError):
    """Raised when a job execution fails."""
    
    def __init__(self, message: str, job_state: int = None, object_name: str = None):
        super().__init__(message)
        self.job_state = job_state
        self.object_name = object_name


class IICSPullError(IICSError):
    """Raised when a pull/sync operation fails."""
    
    def __init__(self, message: str, pull_status: str = None):
        super().__init__(message)
        self.pull_status = pull_status


class IICSRollbackError(IICSError):
    """Raised when a rollback operation fails."""
    pass


class IICSConfigError(IICSError):
    """Raised when configuration is missing or invalid."""
    pass
