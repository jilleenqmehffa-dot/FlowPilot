"""Application configuration and shared infrastructure."""

from backend.app.core.exceptions import (
    CRMServiceError,
    InvalidActivityError,
    InvalidOpportunityTransitionError,
    OpportunityOwnerConflictError,
    ResourceNotFoundError,
)

__all__ = [
    "CRMServiceError",
    "InvalidActivityError",
    "InvalidOpportunityTransitionError",
    "OpportunityOwnerConflictError",
    "ResourceNotFoundError",
]
