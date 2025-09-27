import json
import os
import types
import pytest


class DummyChoice:
    def __init__(self, content: str):
        self.message = types.SimpleNamespace(content=content)


class DummyResp:
    def __init__(self, content: str):
        self.choices = [DummyChoice(content)]


class DummyCompletions:
    def create(self, model=None, response_format=None, messages=None, temperature=None):
        # Default content can be overridden per-test via environment var
        content = os.environ.get("TEST_LLM_RESPONSE", "{}")
        return DummyResp(content)


class DummyChat:
    def __init__(self):
        self.completions = DummyCompletions()


class DummyOpenAI:
    def __init__(self):
        self.chat = DummyChat()


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    # Patch OpenAI() constructor used in common_llm
    from openai import OpenAI as RealOpenAI

    def _dummy_ctor(*args, **kwargs):
        return DummyOpenAI()

    monkeypatch.setattr("openai.OpenAI", _dummy_ctor)
    yield
