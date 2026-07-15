document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-search-form]");

    if (!form) {
        return;
    }

    const submitFilters = () => form.requestSubmit();

    form.querySelectorAll("[data-live-filter='immediate']").forEach((filter) => {
        filter.addEventListener("change", submitFilters);
    });

    const priceRange = form.querySelector("[data-price-range]");
    const minPrice = form.querySelector("[data-price-min]");
    const maxPrice = form.querySelector("[data-price-max]");
    const minPriceOutput = form.querySelector("[data-price-min-output]");
    const maxPriceOutput = form.querySelector("[data-price-max-output]");
    const priceTrack = form.querySelector("[data-price-track]");
    const formatPrice = (value) => `${Number(value).toFixed(2)}€`;

    const updatePriceRange = (changedFilter) => {
        if (!priceRange) {
            return;
        }

        if (Number(minPrice.value) > Number(maxPrice.value)) {
            if (changedFilter === minPrice) {
                maxPrice.value = minPrice.value;
            } else {
                minPrice.value = maxPrice.value;
            }
        }

        const catalogueMaximum = Number(maxPrice.max) || 1;
        const start = (Number(minPrice.value) / catalogueMaximum) * 100;
        const end = (Number(maxPrice.value) / catalogueMaximum) * 100;

        minPriceOutput.value = formatPrice(minPrice.value);
        maxPriceOutput.value = formatPrice(maxPrice.value);
        priceTrack.style.setProperty("--price-start", `${start}%`);
        priceTrack.style.setProperty("--price-end", `${end}%`);
    };

    updatePriceRange();

    let priceTimer;

    form.querySelectorAll("[data-live-filter='debounced']").forEach((filter) => {
        filter.addEventListener("input", () => {
            window.clearTimeout(priceTimer);
            updatePriceRange(filter);

            if (!filter.validity.valid) {
                return;
            }

            priceTimer = window.setTimeout(submitFilters, 500);
        });
    });
});
