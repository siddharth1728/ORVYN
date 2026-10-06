"""Core exceptions for ORVYN."""


class OrvynError(Exception):
    """Base exception for all ORVYN domain and application errors."""
    pass


class TaskNotFoundError(OrvynError):
    pass


class InvalidStateTransitionError(OrvynError):
    pass


class CheckpointError(OrvynError):
    pass


class CheckpointNotFoundError(CheckpointError):
    pass


class ProviderNotConfiguredError(OrvynError):
    pass
