import logging

from arches.app.models import models
from arches.app.models.resource import Resource

from arches_resource_version_manager.models import ResourceVersion

logger = logging.getLogger(__name__)


def archive_and_copy_draft(resource_group_id: str, user) -> Resource:
    """
    Archive the current editable Draft by cloning it with a Retired lifecycle
    state, recording the clone in ResourceVersion, then returning the original
    draft resource for further mutation.
    """
    try:
        current_version = ResourceVersion.objects.get(
            resource_group_id=resource_group_id,
            state=ResourceVersion.DRAFT,
            editable=True,
        )
    except ResourceVersion.DoesNotExist:
        raise ValueError(
            f"No editable Draft ResourceVersion found for {resource_group_id!r}."
        )

    draft_resource = models.Resource.objects.get(
        resourceinstanceid=current_version.resourceinstanceid_id
    )
    draft_clone = draft_resource.copy()
    draft_clone.resource_instance_lifecycle_state = (
        models.ResourceInstanceLifecycleState.objects.get(name="Retired")
    )
    draft_clone.save(user=user)

    ResourceVersion.objects.create(
        resource_group_id=resource_group_id,
        resourceinstanceid=draft_clone,
        version=current_version.version,
        payload=current_version.payload,
        editable=False,
        state=ResourceVersion.ARCHIVED,
    )

    return draft_resource


def archive_final_version(resource_group_id: str) -> None:
    """Mark the current Final ResourceVersion as Archived."""
    try:
        version = ResourceVersion.objects.get(
            resource_group_id=resource_group_id,
            state=ResourceVersion.FINAL,
        )
    except ResourceVersion.DoesNotExist:
        raise ValueError(
            f"No Final ResourceVersion found for {resource_group_id!r}."
        )
    version.state = ResourceVersion.ARCHIVED
    version.editable = False
    version.save()
