"""Application configuration and shared infrastructure."""

from backend.app.core.exceptions import (
    CRMServiceError,
    InvalidOpportunityTransitionError,
    OpportunityOwnerConflictError,
    ResourceNotFoundError,
)

__all__ = [
    "CRMServiceError",
    "InvalidOpportunityTransitionError",
    "OpportunityOwnerConflictError",
    "ResourceNotFoundError",
]
