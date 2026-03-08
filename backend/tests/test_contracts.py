import pytest
from pydantic import ValidationError

from app.schemas import AIConsultRequest, CaseCreateRequest, EventCreateRequest


def test_case_create_contract_valid():
    payload = CaseCreateRequest(
        case_code="A40-12345/2026",
        case_type="arbitration_debt",
        client_ref="client_001",
        lawyer_ref="lawyer_007",
        jurisdiction="Россия",
        status="new",
    )
    assert payload.case_code == "A40-12345/2026"


def test_event_create_contract_invalid_dates():
    with pytest.raises(ValidationError):
        EventCreateRequest(
            case_code="A40-12345/2026",
            event_type="court_hearing",
            start_at="not-a-date",
            end_at="2026-03-20T08:00:00.000Z",
            lawyer_chat_id="123456789",
        )


def test_ai_consult_contract_requires_text():
    with pytest.raises(ValidationError):
        AIConsultRequest(
            case_code="A40-12345/2026",
            jurisdiction="Россия",
            document_text="",
        )
