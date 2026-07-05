"""Builds the shared OpenAI client from the OPENAI_API_KEY environment variable.

The key is never hard-coded or read from anywhere else, per the submission
guidelines' secrets-management rules.
"""

import os

from openai import OpenAI


def build_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)
