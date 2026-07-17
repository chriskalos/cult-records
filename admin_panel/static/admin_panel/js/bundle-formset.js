(() => {
    const container = document.querySelector("[data-bundle-formset]");
    const addButton = document.querySelector("[data-add-bundle-component]");
    const template = document.querySelector("[data-empty-bundle-form]");
    const totalForms = document.querySelector("[name='components-TOTAL_FORMS']");

    if (!container || !addButton || !template || !totalForms) {
        return;
    }

    addButton.addEventListener("click", () => {
        const index = Number.parseInt(totalForms.value, 10);
        const wrapper = document.createElement("div");
        wrapper.innerHTML = template.innerHTML.replaceAll("__prefix__", index).trim();
        const row = wrapper.firstElementChild;
        container.append(row);
        totalForms.value = index + 1;
        row.querySelector("select")?.focus();
    });
})();
