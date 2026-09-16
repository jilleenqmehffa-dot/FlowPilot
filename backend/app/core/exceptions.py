"""Business errors raised by CRM services."""


class CRMServiceError(Exception):
    """Base class for expected CRM business errors."""


class ResourceNotFoundError(CRMServiceError, LookupError):
    def __init__(self, resource: str, record_id: int) -> None:
        self.resource = resource
        self.record_id = record_id
        super().__init__(f"{resource} {record_id} was not found")


class InvalidOpportunityTransitionError(CRMServiceError, ValueError):
    """The requested opportunity stage transition is not allowed."""


class OpportunityOwnerConflictError(CRMServiceError, ValueError):
    """An owner reassignment did not identify a different owner."""


class InvalidActivityError(CRMServiceError, ValueError):
    """Activity data violates a business rule not expressible by one field."""


class InvalidTaskError(CRMServiceError, ValueError):
    """Task data violates a business rule not expressible by one field."""


class InvalidTaskTransitionError(CRMServiceError, ValueError):
    """The requested task status transition is not allowed."""
