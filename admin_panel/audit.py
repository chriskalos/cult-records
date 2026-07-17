from .models import AdminActivity


def record_admin_activity(
    *,
    actor,
    action,
    target_type,
    target_identifier,
    target_label,
    summary,
    metadata=None,
):
    return AdminActivity.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_identifier=str(target_identifier),
        target_label=str(target_label),
        summary=summary,
        metadata=metadata or {},
    )
