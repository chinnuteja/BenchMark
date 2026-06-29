"""Model provider abstraction for TENDER-TIMELINE."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class ProviderError(RuntimeError):
    """Raised when a provider cannot run."""


def _prediction_to_raw_output(prediction: dict[str, Any]) -> str:
    return json.dumps(prediction, ensure_ascii=False)


def _fake_naive_prediction(item_id: str) -> dict[str, Any] | str:
    """Worst fake baseline: trap failures on Items 002 and 004."""
    predictions: dict[str, dict[str, Any] | str] = {
        "tt_item_001_late_submission": {
            "governing_clause_id": "Addendum 2 §1 read with ITB 22.1",
            "operative_deadline": "2026-06-14T10:00:00+03:00",
            "action_datetime": "2026-06-14T10:03:00+03:00",
            "precondition_status": "not_evaluated",
            "verdict": "INVALID",
            "failure_reason_code": "LATE_SUBMISSION",
            "citation": {
                "deadline": "Addendum 2 §1; ITB 22.1",
                "submission": "Bidder Action Log",
            },
        },
        "tt_item_002_bid_security_short": {
            "governing_clause_id": "Tender Data Sheet deadline",
            "operative_deadline": "2026-06-10T10:00:00+03:00",
            "action_datetime": "2026-06-14T09:58:00+03:00",
            "required_bid_security_validity_through": "2026-11-05",
            "submitted_bid_security_validity_through": "2026-11-06",
            "precondition_status": "satisfied",
            "verdict": "VALID",
            "failure_reason_code": "VALID",
            "citation": {"rule": "Tender Data Sheet"},
        },
        "tt_item_003_valid_control": {
            "governing_clause_id": "Tender Data Sheet deadline",
            "operative_deadline": "2026-06-14T10:00:00+03:00",
            "action_datetime": "2026-06-14T09:58:00+03:00",
            "required_bid_security_validity_through": "2026-11-09",
            "submitted_bid_security_validity_through": "2026-11-10",
            "precondition_status": "satisfied",
            "verdict": "VALID",
            "failure_reason_code": "VALID",
            "citation": {"rule": "Tender Data Sheet"},
        },
        "tt_item_004_gao_solicitation_impropriety_late": {
            "governing_clause_id": "4 CFR §21.2(a)(2)",
            "operative_deadline": "2026-08-15T23:59:00-04:00",
            "action_datetime": "2026-07-21T09:00:00-04:00",
            "precondition_status": "unsatisfied",
            "verdict": "INVALID",
            "failure_reason_code": "MISSED_PROTEST_WINDOW",
            "citation": {"rule": "4 CFR §21.2(a)(2)", "filing": "Protest Action Log"},
        },
        "tt_item_005_gao_known_basis_timely": {
            "governing_clause_id": "4 CFR §21.2(a)(2)",
            "operative_deadline": "2026-08-15T23:59:00-04:00",
            "action_datetime": "2026-08-14T15:30:00-04:00",
            "precondition_status": "satisfied",
            "verdict": "VALID",
            "failure_reason_code": "VALID",
            "citation": {
                "rule": "4 CFR §21.2(a)(2)",
                "basis_known": "Protest Action Log",
                "filing": "Protest Action Log",
            },
        },
        "tt_item_006_uganda_admin_review_late": (
            "The applicant filed one day after the administrative review window closed."
        ),
    }
    return predictions[item_id]


def _fake_clause_first_prediction(item_id: str) -> dict[str, Any]:
    """Better clause grounding, but still imperfect on Items 002 and 004."""
    predictions: dict[str, dict[str, Any]] = {
        "tt_item_001_late_submission": {
            "governing_clause_id": "Addendum 2 §1 read with ITB 22.1",
            "operative_deadline": "2026-06-14T10:00:00+03:00",
            "action_datetime": "2026-06-14T10:03:00+03:00",
            "precondition_status": "not_evaluated",
            "verdict": "INVALID",
            "failure_reason_code": "LATE_SUBMISSION",
            "citation": {
                "deadline": "Addendum 2 §1; ITB 22.1",
                "submission": "Bidder Action Log",
            },
        },
        "tt_item_002_bid_security_short": {
            "governing_clause_id": "ITB 19.3 read with ITB 18.1 and Addendum 2 §1",
            "operative_deadline": "2026-06-10T10:00:00+03:00",
            "action_datetime": "2026-06-14T09:58:00+03:00",
            "required_bid_security_validity_through": "2026-11-05",
            "submitted_bid_security_validity_through": "2026-11-06",
            "precondition_status": "satisfied",
            "verdict": "VALID",
            "failure_reason_code": "VALID",
            "citation": {
                "rule": "ITB 19.3; ITB 18.1",
                "controlling_deadline": "Addendum 2 §1",
            },
        },
        "tt_item_003_valid_control": {
            "governing_clause_id": "ITB 19.3 read with ITB 18.1 and Addendum 2 §1",
            "operative_deadline": "2026-06-14T10:00:00+03:00",
            "action_datetime": "2026-06-14T09:58:00+03:00",
            "required_bid_security_validity_through": "2026-11-09",
            "submitted_bid_security_validity_through": "2026-11-10",
            "precondition_status": "satisfied",
            "verdict": "VALID",
            "failure_reason_code": "VALID",
            "citation": {
                "rule": "ITB 19.3; ITB 18.1",
                "controlling_deadline": "Addendum 2 §1",
            },
        },
        "tt_item_004_gao_solicitation_impropriety_late": {
            "governing_clause_id": "4 CFR §21.2(a)(2)",
            "operative_deadline": "2026-08-15T23:59:00-04:00",
            "action_datetime": "2026-07-21T09:00:00-04:00",
            "precondition_status": "unsatisfied",
            "verdict": "INVALID",
            "failure_reason_code": "MISSED_PROTEST_WINDOW",
            "citation": {"rule": "4 CFR §21.2(a)(2)", "filing": "Protest Action Log"},
        },
        "tt_item_005_gao_known_basis_timely": {
            "governing_clause_id": "4 CFR §21.2(a)(2)",
            "operative_deadline": "2026-08-15T23:59:00-04:00",
            "action_datetime": "2026-08-14T15:30:00-04:00",
            "precondition_status": "satisfied",
            "verdict": "VALID",
            "failure_reason_code": "VALID",
            "citation": {
                "rule": "4 CFR §21.2(a)(2)",
                "basis_known": "Protest Action Log",
                "filing": "Protest Action Log",
            },
        },
        "tt_item_006_uganda_admin_review_late": {
            "governing_clause_id": "Demo Rule 10.1",
            "operative_deadline": "2026-09-11T23:59:00+03:00",
            "action_datetime": "2026-09-12T10:00:00+03:00",
            "precondition_status": "unsatisfied",
            "verdict": "INVALID",
            "failure_reason_code": "MISSED_PROTEST_WINDOW",
            "citation": {
                "rule": "Demo Rule 10.1",
                "receipt": "Decision Timeline",
                "filing": "Review Filing Log",
            },
        },
    }
    return predictions[item_id]


def _fake_event_graph_first_prediction(item_id: str) -> dict[str, Any]:
    """Strongest fake baseline; Item 004 still uses wrong failure code."""
    predictions: dict[str, dict[str, Any]] = {
        "tt_item_001_late_submission": {
            "governing_clause_id": "Addendum 2 §1 read with ITB 22.1",
            "operative_deadline": "2026-06-14T10:00:00+03:00",
            "action_datetime": "2026-06-14T10:03:00+03:00",
            "precondition_status": "not_evaluated",
            "verdict": "INVALID",
            "failure_reason_code": "LATE_SUBMISSION",
            "citation": {
                "deadline": "Addendum 2 §1; ITB 22.1",
                "submission": "Bidder Action Log",
            },
        },
        "tt_item_002_bid_security_short": {
            "governing_clause_id": "ITB 19.3 read with ITB 18.1 and Addendum 2 §1",
            "operative_deadline": "2026-06-14T10:00:00+03:00",
            "action_datetime": "2026-06-14T09:58:00+03:00",
            "required_bid_security_validity_through": "2026-11-09",
            "submitted_bid_security_validity_through": "2026-11-06",
            "precondition_status": "unsatisfied",
            "verdict": "INVALID",
            "failure_reason_code": "INSUFFICIENT_BID_SECURITY_VALIDITY",
            "citation": {
                "rule": "ITB 19.3; ITB 18.1",
                "controlling_deadline": "Addendum 2 §1",
                "instrument": "Bid Security Instrument",
            },
        },
        "tt_item_003_valid_control": {
            "governing_clause_id": "ITB 19.3 read with ITB 18.1 and Addendum 2 §1",
            "operative_deadline": "2026-06-14T10:00:00+03:00",
            "action_datetime": "2026-06-14T09:58:00+03:00",
            "required_bid_security_validity_through": "2026-11-09",
            "submitted_bid_security_validity_through": "2026-11-10",
            "precondition_status": "satisfied",
            "verdict": "VALID",
            "failure_reason_code": "VALID",
            "citation": {
                "rule": "ITB 19.3; ITB 18.1",
                "controlling_deadline": "Addendum 2 §1",
            },
        },
        "tt_item_004_gao_solicitation_impropriety_late": {
            "governing_clause_id": "4 CFR §21.2(a)(1)",
            "operative_deadline": "2026-07-20T17:00:00-04:00",
            "action_datetime": "2026-07-21T09:00:00-04:00",
            "precondition_status": "unsatisfied",
            "verdict": "INVALID",
            "failure_reason_code": "ADDENDUM_OVERRIDE_IGNORED",
            "citation": {
                "rule": "4 CFR §21.2(a)(1)",
                "proposal_deadline": "Solicitation Timeline",
                "filing": "Protest Action Log",
            },
        },
        "tt_item_005_gao_known_basis_timely": {
            "governing_clause_id": "4 CFR §21.2(a)(2)",
            "operative_deadline": "2026-08-15T23:59:00-04:00",
            "action_datetime": "2026-08-14T15:30:00-04:00",
            "precondition_status": "satisfied",
            "verdict": "VALID",
            "failure_reason_code": "VALID",
            "citation": {
                "rule": "4 CFR §21.2(a)(2)",
                "basis_known": "Protest Action Log",
                "filing": "Protest Action Log",
            },
        },
        "tt_item_006_uganda_admin_review_late": {
            "governing_clause_id": "Demo Rule 10.1",
            "operative_deadline": "2026-09-11T23:59:00+03:00",
            "action_datetime": "2026-09-12T10:00:00+03:00",
            "precondition_status": "unsatisfied",
            "verdict": "INVALID",
            "failure_reason_code": "MISSED_PROTEST_WINDOW",
            "citation": {
                "rule": "Demo Rule 10.1",
                "receipt": "Decision Timeline",
                "filing": "Review Filing Log",
            },
        },
    }
    return predictions[item_id]


def _call_fake_provider(
    model: str,
    prompt: str,
    item_id: str,
    prompt_name: str,
) -> dict[str, Any]:
    del model, prompt  # fake provider is deterministic; prompt is not echoed back.

    if prompt_name == "naive":
        payload = _fake_naive_prediction(item_id)
    elif prompt_name == "clause_first":
        payload = _fake_clause_first_prediction(item_id)
    elif prompt_name == "event_graph_first":
        payload = _fake_event_graph_first_prediction(item_id)
    else:
        raise ProviderError(f"Unknown fake prompt_name: {prompt_name}")

    if isinstance(payload, str):
        raw_output = payload
    else:
        raw_output = _prediction_to_raw_output(payload)

    return {
        "raw_output": raw_output,
        "latency_ms": 0,
        "usage": {"provider_label": "fake/sample", "note": "Deterministic fake output for pipeline validation"},
    }


def _call_azure_openai_provider(model: str, prompt: str) -> dict[str, Any]:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    deployment = model or os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

    if not api_key:
        raise ProviderError("AZURE_OPENAI_API_KEY is not set")
    if not endpoint:
        raise ProviderError("AZURE_OPENAI_ENDPOINT is not set")
    if not deployment:
        raise ProviderError(
            "Azure deployment not set; pass --model or set AZURE_OPENAI_DEPLOYMENT"
        )

    try:
        from openai import AzureOpenAI
    except ImportError as exc:
        raise ProviderError(
            "openai package is not installed; install with pip install 'tender-timeline[providers]'"
        ) from exc

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=api_key,
    )
    started = time.perf_counter()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=16384,
        model=deployment,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    raw_output = response.choices[0].message.content or ""
    usage: dict[str, Any] = {}
    if response.usage is not None:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
    return {"raw_output": raw_output, "latency_ms": latency_ms, "usage": usage}


def _call_openai_provider(model: str, prompt: str) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ProviderError("OPENAI_API_KEY is not set")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ProviderError(
            "openai package is not installed; install with pip install 'tender-timeline[providers]'"
        ) from exc

    client = OpenAI(api_key=api_key)
    request_kwargs: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        # Reasoning-family models (gpt-5.x, o-series) count reasoning tokens against
        # the completion budget; give enough room to also emit the JSON answer.
        "max_completion_tokens": 16384,
    }
    started = time.perf_counter()
    try:
        # Deterministic decoding when the model supports it.
        response = client.chat.completions.create(temperature=0, **request_kwargs)
    except Exception as exc:  # noqa: BLE001 - some models reject non-default temperature
        if "temperature" in str(exc).lower():
            response = client.chat.completions.create(**request_kwargs)
        else:
            raise
    latency_ms = int((time.perf_counter() - started) * 1000)
    raw_output = response.choices[0].message.content or ""
    usage = {}
    if response.usage is not None:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
    return {"raw_output": raw_output, "latency_ms": latency_ms, "usage": usage}


def _call_anthropic_provider(model: str, prompt: str) -> dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ProviderError("ANTHROPIC_API_KEY is not set")

    try:
        import anthropic
    except ImportError as exc:
        raise ProviderError(
            "anthropic package is not installed; install with pip install 'tender-timeline[providers]'"
        ) from exc

    client = anthropic.Anthropic(api_key=api_key)
    started = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    text_parts = [block.text for block in response.content if block.type == "text"]
    raw_output = "\n".join(text_parts)
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return {"raw_output": raw_output, "latency_ms": latency_ms, "usage": usage}


def _call_google_provider(model: str, prompt: str) -> dict[str, Any]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ProviderError("GOOGLE_API_KEY is not set")

    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise ProviderError(
            "google-generativeai package is not installed; install with pip install 'tender-timeline[providers]'"
        ) from exc

    genai.configure(api_key=api_key)
    started = time.perf_counter()
    gemini_model = genai.GenerativeModel(model)
    response = gemini_model.generate_content(
        prompt,
        generation_config={"temperature": 0},
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    raw_output = getattr(response, "text", "") or ""
    usage: dict[str, Any] = {}
    metadata = getattr(response, "usage_metadata", None)
    if metadata is not None:
        usage = {
            "prompt_token_count": getattr(metadata, "prompt_token_count", None),
            "candidates_token_count": getattr(metadata, "candidates_token_count", None),
            "total_token_count": getattr(metadata, "total_token_count", None),
        }
    return {"raw_output": raw_output, "latency_ms": latency_ms, "usage": usage}


def call_model(
    provider: str,
    model: str,
    prompt: str,
    item_id: str,
    prompt_name: str,
) -> dict[str, Any]:
    """Call a model provider and return raw output metadata."""
    provider_key = provider.strip().lower()

    if provider_key == "fake":
        return _call_fake_provider(model, prompt, item_id, prompt_name)
    if provider_key in {"azure", "azure_openai"}:
        return _call_azure_openai_provider(model, prompt)
    if provider_key == "openai":
        return _call_openai_provider(model, prompt)
    if provider_key == "anthropic":
        return _call_anthropic_provider(model, prompt)
    if provider_key == "google":
        return _call_google_provider(model, prompt)

    raise ProviderError(f"Unsupported provider: {provider}")
