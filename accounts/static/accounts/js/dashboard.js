(() => {
    const confirmationMessage = (
        "Marking this order as delivered will remove it from your dashboard. "
        + "This cannot be undone. Continue?"
    );

    document.addEventListener("submit", (event) => {
        const form = event.target.closest("form[data-delivery-confirmation]");
        if (form && !window.confirm(confirmationMessage)) {
            event.preventDefault();
        }
    });
})();
