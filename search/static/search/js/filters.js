document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-search-form]");

    if (!form) {
        return;
    }

    const submitFilters = () => form.requestSubmit();

    form.querySelectorAll("[data-live-filter='immediate']").forEach((filter) => {
        filter.addEventListener("change", submitFilters);
    });

    let priceTimer;

    form.querySelectorAll("[data-live-filter='debounced']").forEach((filter) => {
        filter.addEventListener("input", () => {
            window.clearTimeout(priceTimer);

            if (!filter.validity.valid) {
                return;
            }

            priceTimer = window.setTimeout(submitFilters, 500);
        });
    });
});
