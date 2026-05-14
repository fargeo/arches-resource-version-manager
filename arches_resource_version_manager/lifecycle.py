import logging

from arches.app.models import models
from arches.app.models.resource import Resource

from arches_resource_version_manager.models import VersionedResource

logger = logging.getLogger(__name__)


def archive_and_copy_draft(resource_group_id: str, user) -> Resource:
    """
    Archive the current editable Draft by cloning it with a Retired lifecycle
    state, recording the clone in VersionedResource, then returning the original
    draft resource for further mutation.
    """
    try:
        current_version = VersionedResource.objects.get(
            resource_group_id=resource_group_id,
            editable=True,
        )
    except VersionedResource.DoesNotExist:
        raise ValueError(
            f"No editable Draft VersionedResource found for {resource_group_id!r}."
        )

    draft_resource = models.Resource.objects.get(pk=current_version.pk)
    draft_clone = draft_resource.copy()
    draft_clone.resource_instance_lifecycle_state = (
        models.ResourceInstanceLifecycleState.objects.get(name="Retired")
    )
    draft_clone.save(user=user)

    VersionedResource.objects.create(
        resourceinstance_id=draft_clone.resourceinstanceid,
        resource_group_id=resource_group_id,
        version=current_version.version,
        payload=current_version.payload,
        editable=False,
    )

    return draft_resource
