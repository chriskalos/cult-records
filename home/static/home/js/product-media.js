(() => {
    const supportsHover = window.matchMedia("(hover: hover) and (pointer: fine)");
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

    if (!supportsHover.matches || prefersReducedMotion.matches) {
        return;
    }

    const activeMedia = new Map();

    document.querySelectorAll("[data-product-media]").forEach((media) => {
        const object = media.querySelector("[data-product-media-object]");
        const interactionSurface = media.closest("[data-product-card]") || media;

        if (!object) {
            return;
        }

        const maximumTilt = media.dataset.productFormat === "CD" ? 9 : 8;
        let animationFrame;
        let isActive = false;

        const reset = () => {
            if (!isActive) {
                return;
            }

            isActive = false;
            activeMedia.delete(media);
            window.cancelAnimationFrame(animationFrame);
            media.classList.remove("is-active");
            media.style.setProperty("--media-rotate-x", "0deg");
            media.style.setProperty("--media-rotate-y", "0deg");
            media.style.setProperty("--media-scale", "1");
        };

        const facePointer = (event) => {
            const bounds = media.getBoundingClientRect();
            const isInside = (
                event.clientX >= bounds.left
                && event.clientX <= bounds.right
                && event.clientY >= bounds.top
                && event.clientY <= bounds.bottom
            );

            if (!isInside) {
                reset();
                return;
            }

            const horizontalPosition = (event.clientX - bounds.left) / bounds.width;
            const verticalPosition = (event.clientY - bounds.top) / bounds.height;
            const rotateX = (0.5 - verticalPosition) * maximumTilt * 2;
            const rotateY = (horizontalPosition - 0.5) * maximumTilt * 2;

            isActive = true;
            activeMedia.set(media, reset);
            window.cancelAnimationFrame(animationFrame);
            animationFrame = window.requestAnimationFrame(() => {
                media.classList.add("is-active");
                media.style.setProperty("--media-rotate-x", `${rotateX.toFixed(2)}deg`);
                media.style.setProperty("--media-rotate-y", `${rotateY.toFixed(2)}deg`);
                media.style.setProperty("--media-scale", "1.025");
            });
        };

        interactionSurface.addEventListener("pointermove", facePointer, { passive: true });
        interactionSurface.addEventListener("pointerleave", reset);
        interactionSurface.addEventListener("pointercancel", reset);
    });

    document.addEventListener("pointermove", (event) => {
        activeMedia.forEach((reset, media) => {
            const bounds = media.getBoundingClientRect();
            const isInside = (
                event.clientX >= bounds.left
                && event.clientX <= bounds.right
                && event.clientY >= bounds.top
                && event.clientY <= bounds.bottom
            );

            if (!isInside) {
                reset();
            }
        });
    }, { passive: true });
})();
