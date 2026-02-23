"""Tests for the reference data API endpoints (systems, VTTs, special events)."""

from unittest.mock import patch

from website.exceptions import NotFoundError


class TestListSystems:
    """Tests for GET /api/v1/systems/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/systems/")
        assert response.status_code == 403

    @patch("website.api.reference_data.system_service")
    def test_returns_list(self, mock_service, api_client, auth_headers_user):
        """Returns JSON list of systems."""
        mock_service.get_all.return_value = []
        response = api_client.get("/api/v1/systems/", headers=auth_headers_user)
        assert response.status_code == 200
        assert response.get_json() == []
        mock_service.get_all.assert_called_once()

    @patch("website.api.reference_data.system_service")
    def test_returns_system_data(self, mock_service, api_client, auth_headers_user):
        """Returns serialised system objects."""
        from unittest.mock import MagicMock

        system = MagicMock()
        system.to_dict.return_value = {"id": 1, "name": "D&D 5e", "icon": None}
        mock_service.get_all.return_value = [system]

        response = api_client.get("/api/v1/systems/", headers=auth_headers_user)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["name"] == "D&D 5e"


class TestGetSystem:
    """Tests for GET /api/v1/systems/<id>/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/systems/1/")
        assert response.status_code == 403

    @patch("website.api.reference_data.system_service")
    def test_returns_system(self, mock_service, api_client, auth_headers_user):
        """Returns a single system by ID."""
        from unittest.mock import MagicMock

        system = MagicMock()
        system.to_dict.return_value = {"id": 1, "name": "D&D 5e", "icon": None}
        mock_service.get_by_id.return_value = system

        response = api_client.get("/api/v1/systems/1/", headers=auth_headers_user)
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == 1
        mock_service.get_by_id.assert_called_once_with(1)

    @patch("website.api.reference_data.system_service")
    def test_not_found(self, mock_service, api_client, auth_headers_user):
        """Returns 404 for non-existent system."""
        mock_service.get_by_id.side_effect = NotFoundError(
            "System not found", resource_type="System", resource_id=999
        )
        response = api_client.get("/api/v1/systems/999/", headers=auth_headers_user)
        assert response.status_code == 404


class TestListVtts:
    """Tests for GET /api/v1/vtts/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/vtts/")
        assert response.status_code == 403

    @patch("website.api.reference_data.vtt_service")
    def test_returns_list(self, mock_service, api_client, auth_headers_user):
        """Returns JSON list of VTTs."""
        mock_service.get_all.return_value = []
        response = api_client.get("/api/v1/vtts/", headers=auth_headers_user)
        assert response.status_code == 200
        assert response.get_json() == []


class TestGetVtt:
    """Tests for GET /api/v1/vtts/<id>/."""

    @patch("website.api.reference_data.vtt_service")
    def test_returns_vtt(self, mock_service, api_client, auth_headers_user):
        """Returns a single VTT by ID."""
        from unittest.mock import MagicMock

        vtt = MagicMock()
        vtt.to_dict.return_value = {"id": 1, "name": "Foundry VTT", "icon": None}
        mock_service.get_by_id.return_value = vtt

        response = api_client.get("/api/v1/vtts/1/", headers=auth_headers_user)
        assert response.status_code == 200
        assert response.get_json()["name"] == "Foundry VTT"

    @patch("website.api.reference_data.vtt_service")
    def test_not_found(self, mock_service, api_client, auth_headers_user):
        """Returns 404 for non-existent VTT."""
        mock_service.get_by_id.side_effect = NotFoundError(
            "Vtt not found", resource_type="Vtt", resource_id=999
        )
        response = api_client.get("/api/v1/vtts/999/", headers=auth_headers_user)
        assert response.status_code == 404


class TestListSpecialEvents:
    """Tests for GET /api/v1/special-events/."""

    def test_requires_auth(self, api_client):
        """Endpoint requires authentication."""
        response = api_client.get("/api/v1/special-events/")
        assert response.status_code == 403

    @patch("website.api.reference_data.special_event_service")
    def test_returns_all(self, mock_service, api_client, auth_headers_user):
        """Returns all special events by default."""
        mock_service.get_all.return_value = []
        response = api_client.get("/api/v1/special-events/", headers=auth_headers_user)
        assert response.status_code == 200
        mock_service.get_all.assert_called_once_with(active_only=False)

    @patch("website.api.reference_data.special_event_service")
    def test_active_only_filter(self, mock_service, api_client, auth_headers_user):
        """Passing active=true filters to active events only."""
        mock_service.get_all.return_value = []
        response = api_client.get("/api/v1/special-events/?active=true", headers=auth_headers_user)
        assert response.status_code == 200
        mock_service.get_all.assert_called_once_with(active_only=True)


class TestGetSpecialEvent:
    """Tests for GET /api/v1/special-events/<id>/."""

    @patch("website.api.reference_data.special_event_service")
    def test_returns_event(self, mock_service, api_client, auth_headers_user):
        """Returns a single special event by ID."""
        from unittest.mock import MagicMock

        event = MagicMock()
        event.to_dict.return_value = {
            "id": 1,
            "name": "Halloween",
            "emoji": None,
            "color": None,
            "active": True,
        }
        mock_service.get_by_id.return_value = event

        response = api_client.get("/api/v1/special-events/1/", headers=auth_headers_user)
        assert response.status_code == 200
        assert response.get_json()["name"] == "Halloween"

    @patch("website.api.reference_data.special_event_service")
    def test_not_found(self, mock_service, api_client, auth_headers_user):
        """Returns 404 for non-existent special event."""
        mock_service.get_by_id.side_effect = NotFoundError(
            "SpecialEvent not found", resource_type="SpecialEvent", resource_id=999
        )
        response = api_client.get("/api/v1/special-events/999/", headers=auth_headers_user)
        assert response.status_code == 404
