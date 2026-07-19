(() => {
    const selectAll = document.querySelector("[data-select-all-reviews]");
    const checkboxes = [...document.querySelectorAll("[data-review-checkbox]")];

    if (!selectAll || !checkboxes.length) {
        return;
    }

    const updateSelectAll = () => {
        const selectedCount = checkboxes.filter((checkbox) => checkbox.checked).length;
        selectAll.checked = selectedCount === checkboxes.length;
        selectAll.indeterminate = selectedCount > 0 && selectedCount < checkboxes.length;
    };

    selectAll.addEventListener("change", () => {
        checkboxes.forEach((checkbox) => {
            checkbox.checked = selectAll.checked;
        });
        updateSelectAll();
    });
    checkboxes.forEach((checkbox) => checkbox.addEventListener("change", updateSelectAll));
})();
