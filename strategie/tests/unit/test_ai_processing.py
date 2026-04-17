from unittest.mock import MagicMock, patch

from modules.ai_processing.application.schemas import AnalysisInput, AnalysisOutput
from modules.ai_processing.application.service import analyse_text


def make_mock_output():
    return AnalysisOutput(
        summary="Test summary.",
        action_items=["Do something"],
        persons=["Ondra", "Kristy"],
        recommendations=["Start now"],
    )


@patch("modules.ai_processing.application.service.anthropic.Anthropic")
@patch("modules.ai_processing.application.service.log_analysis")
def test_analyse_text_returns_output(mock_audit, mock_anthropic):
    # Mock LLM response
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value.content = [
        MagicMock(text='{"summary": "Test summary.", "action_items": ["Do something"], "persons": ["Ondra", "Kristy"], "recommendations": ["Start now"]}')
    ]

    result = analyse_text(AnalysisInput(text="We met and agreed on next steps."))

    assert isinstance(result, AnalysisOutput)
    assert result.summary == "Test summary."
    assert "Ondra" in result.persons
    assert mock_audit.called
