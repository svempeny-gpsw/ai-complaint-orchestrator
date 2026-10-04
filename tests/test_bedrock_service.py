from unittest.mock import Mock, patch

from app.services import bedrock_service


def test_bedrock_client_is_cached_and_bounded():
    session = Mock()
    client = Mock()
    session.client.return_value = client
    bedrock_service._create_bedrock_client.cache_clear()

    try:
        with patch.object(
            bedrock_service.boto3,
            "Session",
            return_value=session,
        ) as mock_session:
            first = bedrock_service._create_bedrock_client()
            second = bedrock_service._create_bedrock_client()

        assert first is client
        assert second is client
        mock_session.assert_called_once_with(
            profile_name=bedrock_service.settings.aws_profile,
            region_name=bedrock_service.settings.aws_region,
        )
        session.client.assert_called_once_with(
            "bedrock-runtime",
            config=bedrock_service.BEDROCK_CLIENT_CONFIG,
        )
        assert bedrock_service.BEDROCK_CLIENT_CONFIG.connect_timeout == 5
        assert bedrock_service.BEDROCK_CLIENT_CONFIG.read_timeout == 30
        assert bedrock_service.BEDROCK_CLIENT_CONFIG.retries == {
            "total_max_attempts": 3,
            "mode": "standard",
        }
    finally:
        bedrock_service._create_bedrock_client.cache_clear()
