from django.db.models import Count, Q
from django.shortcuts import render
from django.templatetags.static import static

from .access import enlightened_required
from .models import ArchiveDocument, AssetObservation, Directive, HumanAsset


def _portrait_url(asset):
    if asset.uploaded_portrait:
        return asset.uploaded_portrait.url
    return static(asset.portrait)


@enlightened_required
def dashboard(request):
    assets = list(
        HumanAsset.objects.filter(is_visible=True).prefetch_related("observations")
    )
    selected_code = request.GET.get("asset", "")
    selected_asset = next(
        (asset for asset in assets if asset.asset_code == selected_code),
        assets[0] if assets else None,
    )
    asset_stats = HumanAsset.objects.filter(is_visible=True).aggregate(
        total=Count("pk"),
        active=Count("pk", filter=Q(status=HumanAsset.Status.ACTIVE)),
        uncertain=Count(
            "pk",
            filter=Q(
                status__in=(
                    HumanAsset.Status.MISPLACED,
                    HumanAsset.Status.DISPUTED,
                )
            ),
        ),
    )
    map_assets = [
        {
            "code": asset.asset_code,
            "name": asset.name,
            "alias": asset.alias,
            "status": asset.status,
            "statusLabel": asset.get_status_display(),
            "location": asset.location_label,
            "latitude": float(asset.latitude),
            "longitude": float(asset.longitude),
            "portrait": _portrait_url(asset),
            "role": asset.network_role,
            "cover": asset.civilian_cover,
            "joined": asset.joined_on.strftime("%d %B %Y"),
            "lastContact": asset.last_contact.strftime("%d %B %Y"),
            "consensus": asset.get_consensus_display(),
            "exposure": asset.get_exposure_display(),
            "summary": asset.summary,
            "notes": asset.network_notes,
            "irregularity": asset.known_irregularity,
            "observations": [
                {
                    "reference": observation.reference,
                    "date": observation.observed_on.strftime("%d %B %Y"),
                    "kind": observation.get_kind_display(),
                    "summary": observation.summary,
                }
                for observation in asset.observations.all()[:3]
            ],
        }
        for asset in assets
    ]
    return render(
        request,
        "ham/dashboard.html",
        {
            "assets": assets,
            "selected_asset": selected_asset,
            "asset_stats": asset_stats,
            "map_assets": map_assets,
            "directives": Directive.objects.filter(is_active=True),
            "observations": AssetObservation.objects.select_related("asset")[:8],
            "archive_documents": ArchiveDocument.objects.filter(is_visible=True),
        },
    )
