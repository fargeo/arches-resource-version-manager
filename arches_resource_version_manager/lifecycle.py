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
            state=VersionedResource.DRAFT,
            editable=True,
        )
    except VersionedResource.DoesNotExist:
        raise ValueError(
            f"No editable Draft VersionedResource found for {resource_group_id!r}."
        )

    draft_resource = models.Resource.objects.get(
        resourceinstanceid=current_version.resourceinstanceid_id
    )
    draft_clone = draft_resource.copy()
    draft_clone.resource_instance_lifecycle_state = (
        models.ResourceInstanceLifecycleState.objects.get(name="Retired")
    )
    draft_clone.save(user=user)

    VersionedResource.objects.create(
        resource_group_id=resource_group_id,
        resourceinstanceid=draft_clone,
        version=current_version.version,
        payload=current_version.payload,
        editable=False,
        state=VersionedResource.ARCHIVED,
    )

    return draft_resource


def archive_final_version(resource_group_id: str) -> None:
    """Mark the current Final VersionedResource as Archived."""
    try:
        version = VersionedResource.objects.get(
            resource_group_id=resource_group_id,
            state=VersionedResource.FINAL,
        )
    except VersionedResource.DoesNotExist:
        raise ValueError(f"No Final VersionedResource found for {resource_group_id!r}.")
    version.state = VersionedResource.ARCHIVED
    version.editable = False
    version.save()
