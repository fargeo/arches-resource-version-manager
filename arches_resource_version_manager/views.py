import json
import logging

from oauth2_provider.models import AccessToken
from oauth2_provider.views.generic import ProtectedResourceView

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from arches.app.utils.response import JSONResponse

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class ResourceVersionSyncView(ProtectedResourceView):
    """
    Base view for external-system sync endpoints that create or update
    versioned Arches resource instances.

    Subclasses must define:
      - graph_id: str  — the target graph UUID
      - process_resource(payload, user) -> (resource, created)  — upsert logic
    """

    graph_id: str = NotImplemented

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, ValueError) as exc:
            return JSONResponse({"error": f"Invalid JSON: {exc}"}, status=400)

        try:
            auth_header = request.headers.get("Authorization", "")
            token_str = auth_header.replace("Bearer ", "")
            try:
                token = AccessToken.objects.get(token=token_str)
            except AccessToken.DoesNotExist:
                return JSONResponse({"error": "Invalid token"}, status=401)
            resource, created = self.process_resource(payload, token.application.user)
        except Exception:
            logger.exception("Error processing sync payload")
            return JSONResponse(
                {"error": "Internal server error — see server logs for details"},
                status=500,
            )

        return JSONResponse(
            {
                "resourceinstanceid": str(resource.resourceinstanceid),
                "created": created,
                "graph_id": self.graph_id,
            },
            status=201 if created else 200,
        )

    def process_resource(self, payload: dict, user) -> tuple:
        raise NotImplementedError(
            "Subclasses must implement process_resource(payload, user)."
        )
