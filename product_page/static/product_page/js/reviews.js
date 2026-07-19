(() => {
    const ajaxHeaders = {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
    };

    const setFeedback = (message, isError = false) => {
        const feedback = document.querySelector("#review-feedback");
        if (!feedback) {
            return;
        }

        feedback.textContent = message;
        feedback.classList.toggle("is-error", isError);
    };

    const setFormDisabled = (form, isDisabled) => {
        form?.querySelectorAll("button, input, textarea").forEach((control) => {
            control.disabled = isDisabled;
        });
    };

    const focusReviewControl = () => {
        const invalidControl = document.querySelector(
            '#reviews [aria-invalid="true"], #reviews input[name="rating"]:checked, #reviews textarea'
        );
        invalidControl?.focus({ preventScroll: true });
    };

    const requestReviewMarkup = async (url, options = {}, form = null) => {
        const reviewSection = document.querySelector("#reviews");
        reviewSection?.setAttribute("aria-busy", "true");
        setFormDisabled(form, true);
        setFeedback("");

        try {
            const response = await fetch(url, {
                credentials: "same-origin",
                ...options,
                headers: {
                    ...ajaxHeaders,
                    ...options.headers,
                },
            });

            if (response.redirected) {
                window.location.assign(response.url);
                return;
            }

            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) {
                throw new Error("The review response was not JSON.");
            }

            const payload = await response.json();
            if (response.status === 401 && payload.redirect_url) {
                window.location.assign(payload.redirect_url);
                return;
            }
            if (!payload.html) {
                throw new Error("The review response did not include updated markup.");
            }

            document.querySelector("#reviews")?.replaceWith(
                document.createRange().createContextualFragment(payload.html)
            );

            const message = payload.message || (
                response.ok ? "" : "Check the highlighted fields and try again."
            );
            setFeedback(message, !response.ok);

            if (!response.ok || options.method === "GET") {
                focusReviewControl();
            }
        } catch (error) {
            setFeedback(
                "The review could not be updated. Check your connection and try again.",
                true
            );
        } finally {
            document.querySelector("#reviews")?.removeAttribute("aria-busy");
            if (form?.isConnected) {
                setFormDisabled(form, false);
            }
        }
    };

    document.addEventListener("change", (event) => {
        const input = event.target.closest("[data-star-rating] .review-rating__input");
        if (!input) {
            return;
        }

        const value = input.closest("fieldset")?.querySelector("[data-rating-value]");
        if (value) {
            value.textContent = `${input.value} out of 5 stars selected`;
        }
    });

    document.addEventListener("keydown", (event) => {
        const input = event.target.closest("[data-star-rating] .review-rating__input");
        const ratingKeys = [
            "ArrowLeft",
            "ArrowRight",
            "ArrowDown",
            "ArrowUp",
            "Home",
            "End",
        ];
        if (!input || !ratingKeys.includes(event.key)) {
            return;
        }

        const inputs = [...input.closest("[data-star-rating]").querySelectorAll(".review-rating__input")];
        const currentIndex = inputs.indexOf(input);
        let nextIndex = currentIndex;

        if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
            nextIndex = Math.max(0, currentIndex - 1);
        } else if (event.key === "ArrowRight" || event.key === "ArrowUp") {
            nextIndex = Math.min(inputs.length - 1, currentIndex + 1);
        } else if (event.key === "Home") {
            nextIndex = 0;
        } else if (event.key === "End") {
            nextIndex = inputs.length - 1;
        }

        event.preventDefault();
        inputs[nextIndex].checked = true;
        inputs[nextIndex].focus();
        inputs[nextIndex].dispatchEvent(new Event("change", { bubbles: true }));
    });

    document.addEventListener("click", (event) => {
        const link = event.target.closest("[data-review-load]");
        if (!link) {
            return;
        }

        event.preventDefault();
        requestReviewMarkup(link.href, { method: "GET" });
    });

    document.addEventListener("submit", (event) => {
        const form = event.target.closest("form[data-review-ajax]");
        if (!form) {
            return;
        }

        event.preventDefault();
        if (
            form.matches("[data-review-delete]")
            && !window.confirm("Delete your review? This cannot be undone.")
        ) {
            return;
        }

        requestReviewMarkup(
            form.action,
            {
                method: "POST",
                body: new FormData(form),
            },
            form
        );
    });
})();
