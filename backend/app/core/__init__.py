"""Application configuration and shared infrastructure."""

from backend.app.core.exceptions import (
    CRMServiceError,
    InvalidActivityError,
    InvalidCustomerError,
    InvalidOpportunityTransitionError,
    InvalidTaskError,
    InvalidTaskTransitionError,
    OpportunityOwnerConflictError,
    ResourceNotFoundError,
)

__all__ = [
    "CRMServiceError",
    "InvalidActivityError",
    "InvalidCustomerError",
    "InvalidOpportunityTransitionError",
    "InvalidTaskError",
    "InvalidTaskTransitionError",
    "OpportunityOwnerConflictError",
    "ResourceNotFoundError",
]
