document.querySelectorAll("[data-photo-upload]").forEach(upload => {
  const input = upload.querySelector("[data-photo-input]");
  const preview = upload.querySelector("[data-photo-preview]");
  const error = upload.querySelector("[data-photo-error]");
  const dropzone = upload.querySelector("[data-photo-dropzone]");
  const maxFiles = Number(input.dataset.photoMax);
  const existingFiles = Number(input.dataset.photoExisting || 0);
  let selectedFiles = [];

  function syncInputFiles() {
    const transfer = new DataTransfer();
    selectedFiles.forEach(file => transfer.items.add(file));
    input.files = transfer.files;
  }

  function renderPreviews() {
    preview.querySelectorAll("img[data-preview-url]").forEach(image => {
      URL.revokeObjectURL(image.dataset.previewUrl);
    });
    preview.replaceChildren();

    selectedFiles.forEach((file, index) => {
      const item = document.createElement("div");
      item.className = "photo-preview-item photo-preview-item--selected";

      const image = document.createElement("img");
      image.src = URL.createObjectURL(file);
      image.dataset.previewUrl = image.src;
      image.alt = file.name;

      const removeButton = document.createElement("button");
      removeButton.type = "button";
      removeButton.className = "photo-preview-remove";
      removeButton.textContent = "×";
      removeButton.setAttribute("aria-label", `Remove ${file.name}`);
      removeButton.addEventListener("click", () => {
        selectedFiles.splice(index, 1);
        error.textContent = "";
        syncInputFiles();
        renderPreviews();
      });

      item.append(image, removeButton);
      preview.appendChild(item);
    });
  }

  function addFiles(files) {
    const incomingFiles = Array.from(files);
    if (existingFiles + selectedFiles.length + incomingFiles.length > maxFiles) {
      error.textContent = `You can upload a maximum of ${maxFiles} photos per request.`;
      syncInputFiles();
      return;
    }

    error.textContent = "";
    selectedFiles.push(...incomingFiles);
    syncInputFiles();
    renderPreviews();
  }

  input.addEventListener("change", () => addFiles(input.files));

  if (dropzone) {
    dropzone.addEventListener("click", event => {
      if (event.target !== input) input.click();
    });
    dropzone.addEventListener("dragover", event => {
      event.preventDefault();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });
    dropzone.addEventListener("drop", event => {
      event.preventDefault();
      dropzone.classList.remove("dragover");
      addFiles(event.dataTransfer.files);
    });
  }
});
