"""Custom exception hierarchy for the ORVYN platform."""


class OrvynError(Exception):
    """Base exception for all ORVYN errors."""
    pass


class StateTransitionError(OrvynError):
    """Raised when an illegal state machine transition is attempted."""
    def __init__(self, from_state: str, to_state: str, reason: str = ""):
        message = f"Illegal state transition from '{from_state}' to '{to_state}'."
        if reason:
            message += f" Reason: {reason}"
        super().__init__(message)
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason


class CheckpointError(OrvynError):
    """Raised when a checkpoint cannot be saved or restored."""
    pass


class CheckpointNotFoundError(CheckpointError):
    """Raised when the specified checkpoint token or ID does not exist."""
    pass


class DecisionEngineError(OrvynError):
    """Raised when the decision engine fails to evaluate or classify an action."""
    pass


class TelephonyError(OrvynError):
    """Raised on voice dispatch or call lifecycle failures."""
    pass


class SecurityViolationError(OrvynError):
    """Raised when an unapproved external action is attempted without authorization."""
    pass
