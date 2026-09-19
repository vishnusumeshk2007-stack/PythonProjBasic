document.addEventListener("DOMContentLoaded", function () {
  const categorySelect = document.getElementById("categoryFilter");
  if (categorySelect) {
    categorySelect.addEventListener("change", function () {
      this.form.submit();
    });
  }

  // Confirm before deleting a certificate
  document.querySelectorAll(".delete-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!confirm("Delete this certificate? This cannot be undone.")) {
        e.preventDefault();
      }
    });
  });

  // File input preview name
  const fileInput = document.getElementById("file");
  const fileLabel = document.getElementById("fileLabel");
  if (fileInput && fileLabel) {
    fileInput.addEventListener("change", function () {
      fileLabel.textContent = fileInput.files.length
        ? fileInput.files[0].name
        : "Choose a file (PDF, JPG, PNG)";
    });
  }
});
