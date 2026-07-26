/*
  Lost & Found Client-side JavaScript.
  Handles image uploads preview, form validation feedback, modal handling, and rejection reason toggles.
*/

document.addEventListener('DOMContentLoaded', function () {
    console.log('Lost & Found App Initialized.');

    // Image Upload Live Preview
    const imageInput = document.getElementById('image') || document.querySelector('input[type="file"]');
    const previewContainer = document.getElementById('image-preview');

    if (imageInput && previewContainer) {
        imageInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (event) {
                    previewContainer.innerHTML = `<img src="${event.target.result}" class="img-fluid rounded" alt="Upload Preview">`;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Rejection Reason Toggle on Review Forms
    const actionSelect = document.getElementById('action') || document.querySelector('select[name="action"]');
    const rejectionBox = document.getElementById('rejection-reason-box');

    if (actionSelect && rejectionBox) {
        function toggleRejectionBox() {
            if (actionSelect.value === 'reject') {
                rejectionBox.style.display = 'block';
                const input = rejectionBox.querySelector('textarea, input');
                if (input) input.required = true;
            } else {
                rejectionBox.style.display = 'none';
                const input = rejectionBox.querySelector('textarea, input');
                if (input) input.required = false;
            }
        }

        actionSelect.addEventListener('change', toggleRejectionBox);
        toggleRejectionBox(); // Initial check
    }
});
