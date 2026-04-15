"""Shared custom exceptions for the pipeline."""


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class LLMError(PipelineError):
    """LLM call failed."""
    pass


class APIKeyMissingError(LLMError):
    """API key is not configured."""
    pass


class LLMResponseError(LLMError):
    """LLM returned an error or malformed response."""
    pass
