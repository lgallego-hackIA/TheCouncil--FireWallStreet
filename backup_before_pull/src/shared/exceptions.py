"""
Shared exceptions for theCouncil API system.
"""


class TheCouncilError(Exception):
    """Base exception for all theCouncil errors."""
    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AutomationError(TheCouncilError):
    """Base exception for all automation-related errors."""
    pass


class AutomationNotFoundError(AutomationError):
    """Exception raised when an automation is not found."""
    pass


class EndpointError(TheCouncilError):
    """Base exception for all endpoint-related errors."""
    pass


class EndpointNotFoundError(EndpointError):
    """Exception raised when an endpoint is not found."""
    pass


class DatabaseError(TheCouncilError):
    """Base exception for all database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception raised when a database connection fails."""
    pass


class ConfigurationError(TheCouncilError):
    """Exception raised when there is a configuration error."""
    pass


class ValidationError(TheCouncilError):
    """Exception raised when data validation fails."""
    pass


class AuthenticationError(TheCouncilError):
    """Exception raised when authentication fails."""
    pass


class AuthorizationError(TheCouncilError):
    """Exception raised when authorization fails."""
    pass
