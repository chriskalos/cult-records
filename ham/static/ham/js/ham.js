(() => {
    "use strict";

    const dataNode = document.getElementById("ham-assets-data");
    const mapNode = document.getElementById("ham-map");
    if (!dataNode || !mapNode) {
        return;
    }

    const assets = JSON.parse(dataNode.textContent);
    if (!assets.length) {
        return;
    }

    const assetsByCode = new Map(assets.map((asset) => [asset.code, asset]));
    const markersByCode = new Map();
    const dossier = {
        portrait: document.getElementById("dossier-portrait"),
        code: document.getElementById("dossier-code"),
        status: document.getElementById("dossier-status"),
        name: document.getElementById("dossier-name"),
        alias: document.getElementById("dossier-alias"),
        summary: document.getElementById("dossier-summary"),
        location: document.getElementById("dossier-location"),
        role: document.getElementById("dossier-role"),
        cover: document.getElementById("dossier-cover"),
        joined: document.getElementById("dossier-joined"),
        contact: document.getElementById("dossier-contact"),
        consensus: document.getElementById("dossier-consensus"),
        exposure: document.getElementById("dossier-exposure"),
        irregularity: document.getElementById("dossier-irregularity"),
        notes: document.getElementById("dossier-notes"),
        observations: document.getElementById("dossier-observations"),
    };
    let selectedCode = document.querySelector(".ham-directory-item.active")?.dataset.hamAsset || assets[0].code;
    let activeFilter = "all";
    let map;

    function isVisibleForFilter(asset) {
        if (activeFilter === "active") {
            return asset.status === "active";
        }
        if (activeFilter === "uncertain") {
            return ["silent", "misplaced", "disputed"].includes(asset.status);
        }
        return true;
    }

    function replaceObservationList(asset) {
        dossier.observations.replaceChildren();
        if (!asset.observations.length) {
            const emptyItem = document.createElement("li");
            const emptyLabel = document.createElement("span");
            emptyLabel.textContent = "No records";
            emptyItem.append(emptyLabel, "Silence is not evidence. It is also not helpful.");
            dossier.observations.append(emptyItem);
            return;
        }

        asset.observations.forEach((observation) => {
            const item = document.createElement("li");
            const label = document.createElement("span");
            label.textContent = `${observation.reference} · ${observation.date} · ${observation.kind}`;
            item.append(label, observation.summary);
            dossier.observations.append(item);
        });
    }

    function updateSelectionStyles() {
        document.querySelectorAll(".ham-directory-item").forEach((item) => {
            const selected = item.dataset.hamAsset === selectedCode;
            item.classList.toggle("active", selected);
            item.setAttribute("aria-current", selected ? "true" : "false");
        });

        markersByCode.forEach((marker, code) => {
            const markerElement = marker.getElement()?.querySelector(".ham-map-marker");
            markerElement?.classList.toggle("selected", code === selectedCode);
            marker.setZIndexOffset(code === selectedCode ? 1000 : 0);
        });
    }

    function showAsset(code, options = {}) {
        const asset = assetsByCode.get(code);
        if (!asset) {
            return;
        }

        selectedCode = code;
        dossier.portrait.src = asset.portrait;
        dossier.portrait.alt = `Portrait of ${asset.name}`;
        dossier.code.textContent = asset.code;
        dossier.status.textContent = asset.statusLabel;
        dossier.status.className = `ham-status ham-status-${asset.status}`;
        dossier.name.textContent = asset.name;
        dossier.alias.textContent = `Known as “${asset.alias}”`;
        dossier.summary.textContent = asset.summary;
        dossier.location.textContent = asset.location;
        dossier.role.textContent = asset.role;
        dossier.cover.textContent = asset.cover;
        dossier.joined.textContent = asset.joined;
        dossier.contact.textContent = asset.lastContact;
        dossier.consensus.textContent = asset.consensus;
        dossier.exposure.textContent = asset.exposure;
        dossier.irregularity.textContent = asset.irregularity;
        dossier.notes.textContent = asset.notes;
        replaceObservationList(asset);
        updateSelectionStyles();

        if (options.centerMap && map) {
            map.setView([asset.latitude, asset.longitude], Math.max(map.getZoom(), 5), {animate: false});
        }
        if (options.updateUrl) {
            const nextUrl = new URL(window.location.href);
            nextUrl.searchParams.set("asset", asset.code);
            nextUrl.hash = "asset-dossier";
            window.history.replaceState({}, "", nextUrl);
        }
        if (options.scrollDossier && window.matchMedia("(max-width: 991.98px)").matches) {
            document.getElementById("asset-dossier")?.scrollIntoView({behavior: "smooth", block: "start"});
        }
    }

    function fitVisibleMarkers() {
        if (!map || !window.L) {
            return;
        }
        const visiblePoints = assets
            .filter(isVisibleForFilter)
            .map((asset) => [asset.latitude, asset.longitude]);
        if (visiblePoints.length) {
            map.fitBounds(window.L.latLngBounds(visiblePoints), {padding: [28, 28], maxZoom: 5, animate: false});
        }
    }

    function applyFilter(filter) {
        activeFilter = filter;
        document.querySelectorAll("[data-ham-filter]").forEach((button) => {
            const active = button.dataset.hamFilter === filter;
            button.classList.toggle("active", active);
            button.setAttribute("aria-pressed", active ? "true" : "false");
        });

        assets.forEach((asset) => {
            const visible = isVisibleForFilter(asset);
            const marker = markersByCode.get(asset.code);
            if (marker && map) {
                if (visible && !map.hasLayer(marker)) {
                    marker.addTo(map);
                } else if (!visible && map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            }
            document.querySelectorAll(`.ham-directory-item[data-ham-asset="${asset.code}"]`).forEach((item) => {
                item.hidden = !visible;
            });
        });

        const selectedAsset = assetsByCode.get(selectedCode);
        if (!selectedAsset || !isVisibleForFilter(selectedAsset)) {
            const replacement = assets.find(isVisibleForFilter);
            if (replacement) {
                showAsset(replacement.code);
            }
        }
        fitVisibleMarkers();
    }

    document.querySelectorAll("[data-ham-asset]").forEach((link) => {
        link.addEventListener("click", (event) => {
            const code = link.dataset.hamAsset;
            if (!assetsByCode.has(code)) {
                return;
            }
            event.preventDefault();
            showAsset(code, {centerMap: true, updateUrl: true, scrollDossier: true});
        });
    });

    document.querySelectorAll("[data-ham-filter]").forEach((button) => {
        button.addEventListener("click", () => applyFilter(button.dataset.hamFilter));
    });

    if (window.L) {
        mapNode.replaceChildren();
        map = window.L.map(mapNode, {
            center: [18, 10],
            zoom: 2,
            minZoom: 2,
            maxZoom: 16,
            scrollWheelZoom: false,
            worldCopyJump: true,
        });
        if (window.L.maplibreGL) {
            window.L.maplibreGL({
                style: "https://tiles.openfreemap.org/styles/dark",
            }).addTo(map);
            map.attributionControl.addAttribution(
                '<a href="https://openfreemap.org">OpenFreeMap</a> &copy; OpenMapTiles Data from <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            );
        }

        assets.forEach((asset) => {
            const icon = window.L.divIcon({
                className: "ham-marker-shell",
                html: `<span class="ham-map-marker status-${asset.status}" aria-hidden="true"></span>`,
                iconAnchor: [9, 9],
                iconSize: [18, 18],
            });
            const marker = window.L.marker([asset.latitude, asset.longitude], {
                alt: `View dossier for ${asset.alias}`,
                icon,
                keyboard: true,
                title: `${asset.alias} · ${asset.location}`,
            });
            marker.bindTooltip(`${asset.alias} · ${asset.location}`, {direction: "top", offset: [0, -8]});
            marker.on("click", () => showAsset(asset.code, {updateUrl: true, scrollDossier: true}));
            marker.addTo(map);
            markersByCode.set(asset.code, marker);
        });
        fitVisibleMarkers();
    }

    showAsset(selectedCode);
})();
