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
    const minPriceInput = form.querySelector("[data-price-min-input]");
    const maxPriceInput = form.querySelector("[data-price-max-input]");
    const minPriceSlider = form.querySelector("[data-price-min-slider]");
    const maxPriceSlider = form.querySelector("[data-price-max-slider]");
    const priceTrack = form.querySelector("[data-price-track]");
    const formatPrice = (value) => Number(value).toFixed(2);

    const updatePriceRange = (changedFilter) => {
        if (!priceRange) {
            return true;
        }

        if (changedFilter === minPriceInput) {
            if (minPriceInput.value === "") {
                return false;
            }
            minPriceSlider.value = minPriceInput.value;
            if (Number(minPriceSlider.value) !== Number(minPriceInput.value)) {
                minPriceInput.value = formatPrice(minPriceSlider.value);
            }
        } else if (changedFilter === maxPriceInput) {
            if (maxPriceInput.value === "") {
                return false;
            }
            maxPriceSlider.value = maxPriceInput.value;
            if (Number(maxPriceSlider.value) !== Number(maxPriceInput.value)) {
                maxPriceInput.value = formatPrice(maxPriceSlider.value);
            }
        } else if (changedFilter === minPriceSlider) {
            minPriceInput.value = formatPrice(minPriceSlider.value);
        } else if (changedFilter === maxPriceSlider) {
            maxPriceInput.value = formatPrice(maxPriceSlider.value);
        }

        if (Number(minPriceSlider.value) > Number(maxPriceSlider.value)) {
            if (changedFilter === minPriceInput || changedFilter === minPriceSlider) {
                maxPriceSlider.value = minPriceSlider.value;
                maxPriceInput.value = formatPrice(maxPriceSlider.value);
            } else {
                minPriceSlider.value = maxPriceSlider.value;
                minPriceInput.value = formatPrice(minPriceSlider.value);
            }
        }

        const catalogueMaximum = Number(maxPriceSlider.max) || 1;
        const start = (Number(minPriceSlider.value) / catalogueMaximum) * 100;
        const end = (Number(maxPriceSlider.value) / catalogueMaximum) * 100;

        priceTrack.style.setProperty("--price-start", `${start}%`);
        priceTrack.style.setProperty("--price-end", `${end}%`);
        return minPriceInput.validity.valid && maxPriceInput.validity.valid;
    };

    updatePriceRange();

    let priceTimer;

    const debouncedFilters = [
        ...form.querySelectorAll("[data-live-filter='debounced']"),
        minPriceSlider,
        maxPriceSlider,
    ].filter(Boolean);

    debouncedFilters.forEach((filter) => {
        filter.addEventListener("input", () => {
            window.clearTimeout(priceTimer);

            if (!updatePriceRange(filter) || !filter.validity.valid) {
                return;
            }

            priceTimer = window.setTimeout(submitFilters, 500);
        });
    });
});
