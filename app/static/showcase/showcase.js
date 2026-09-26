(() => {
  const body = document.body;
  const lightbox = document.querySelector("#image-lightbox");
  const lightboxImage = document.querySelector("#lightbox-image");
  const lightboxCaption = document.querySelector("#lightbox-caption");
  const closeButton = document.querySelector(".lightbox-close");

  document.querySelectorAll(".section, .drawing-section, .closing-band").forEach((section) => {
    section.classList.add("reveal");
  });

  if ("IntersectionObserver" in window) {
    body.classList.add("js-ready");
    const observer = new IntersectionObserver((entries, currentObserver) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        currentObserver.unobserve(entry.target);
      });
    }, { threshold: 0.08, rootMargin: "0px 0px -30px 0px" });
    document.querySelectorAll(".reveal").forEach((section) => observer.observe(section));
  }

  document.querySelectorAll(".image-trigger").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      if (!lightbox || typeof lightbox.showModal !== "function") return;
      const image = trigger.querySelector("img");
      lightboxImage.src = trigger.dataset.image || image?.src || "";
      lightboxImage.alt = image?.alt || "建筑模型和图纸预览";
      lightboxCaption.textContent = trigger.dataset.caption || image?.alt || "";
      lightbox.showModal();
      closeButton?.focus();
    });
  });

  closeButton?.addEventListener("click", () => lightbox?.close());
  lightbox?.addEventListener("click", (event) => {
    if (event.target === lightbox) lightbox.close();
  });
  lightbox?.addEventListener("close", () => {
    lightboxImage.removeAttribute("src");
  });
})();
