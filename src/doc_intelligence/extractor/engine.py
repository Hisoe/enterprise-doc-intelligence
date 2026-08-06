"""Structured extraction engine featuring Tenacity retries and self-healing error feedback."""

import logging
from typing import TypeVar

from langfuse import observe
from pydantic import BaseModel, ValidationError
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from doc_intelligence.extractor.client import get_openai_client

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class SelfHealingExtractionError(Exception):
    """Raised when the LLM fails to generate schema-compliant JSON after maximum retries."""

    pass


class ExtractionEngine:
    """Production extraction engine powered by OpenAI Structured Outputs and Tenacity resilience."""

    def __init__(self) -> None:
        self.client, self.model_name = get_openai_client()

    @observe(name="extract-structured-document")
    def extract(self, cleaned_text: str, schema: type[T], max_attempts: int = 3) -> T:
        """Extracts structured data matching `schema` from `cleaned_text`.

        Uses Tenacity to automatically retry up to `max_attempts` times if validation fails,
        injecting the exact Pydantic ValidationError back into prompt context.
        """
        system_prompt = (
            "You are an enterprise document extraction assistant. "
            "Extract structured data from the document text matching the requested schema. "
            "Ensure strict accuracy for numerical totals, financial metrics, and dates."
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"DOCUMENT TEXT:\n\n{cleaned_text}"},
        ]

        attempt_counter = 0

        # Custom logic wrapper around Tenacity's retrying mechanism
        @retry(
            reraise=True,
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            retry=retry_if_exception_type((ValidationError, ValueError)),
            before_sleep=self._log_retry_attempt,
        )
        def _execute_extraction_attempt() -> T:
            nonlocal attempt_counter
            attempt_counter += 1

            logger.info("Running extraction attempt %d of %d...", attempt_counter, max_attempts)

            try:
                # Use OpenAI Structured Parsing API
                completion = self.client.beta.chat.completions.parse(
                    model=self.model_name,
                    messages=messages,
                    response_format=schema,
                    temperature=0.0,
                )

                choice = completion.choices[0]
                if getattr(choice.message, "refusal", None):
                    raise ValueError(f"LLM refused extraction request: {choice.message.refusal}")

                parsed_result = choice.message.parsed
                if parsed_result is not None:
                    return parsed_result

                raise ValueError("LLM returned null parsed response.")

            except (ValidationError, ValueError) as err:
                validation_error_str = str(err)
                logger.warning(
                    "Extraction attempt %d failed validation: %s",
                    attempt_counter,
                    validation_error_str,
                )

                # Preserve conversation history if assistant output exists
                if "completion" in locals() and completion.choices:
                    assistant_text = completion.choices[0].message.content or ""
                    if assistant_text:
                        messages.append({"role": "assistant", "content": assistant_text})

                # Self-Healing Feedback Loop: Append error message back into user context
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"VALIDATION ERROR ENCOUNTERED ON PREVIOUS ATTEMPT:\n"
                            f"{validation_error_str}\n\n"
                            f"Please re-examine the document text and fix this error strictly according to the schema rules."
                        ),
                    }
                )
                raise err

        try:
            return _execute_extraction_attempt()
        except (ValidationError, ValueError) as final_err:
            raise SelfHealingExtractionError(
                f"Failed to extract valid {schema.__name__} after {max_attempts} attempts. "
                f"Last error: {final_err}"
            ) from final_err

    @staticmethod
    def _log_retry_attempt(retry_state: RetryCallState) -> None:
        """Tenacity callback logged prior to waiting for retry."""
        logger.warning(
            "Tenacity self-healing retry triggered (Attempt #%d). Retrying extraction...",
            retry_state.attempt_number,
        )
