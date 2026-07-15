document.querySelectorAll("[data-review-delete]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        if (!window.confirm("Delete your review? This cannot be undone.")) {
            event.preventDefault();
        }
    });
});
