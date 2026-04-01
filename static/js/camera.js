let video = document.getElementById("video");
let canvas = document.getElementById("canvas");
let stream = null;
let cropper = null;
let capturedImageData = null;
let croppedImageData = null;  // Store cropped image data

document.body.classList.add("dark");

function startCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(s => {
            stream = s;
            video.srcObject = stream;
            video.style.display = "block"; // Show video when camera starts
        })
        .catch(() => alert("Camera access denied."));
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        stream = null;
    }
}

function captureImage() {
    if (!stream) {
        alert("Open camera first.");
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    let ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    capturedImageData = canvas.toDataURL("image/jpeg", 0.8);

    stopCamera();

    // Show preview gallery instead of cropper
    showPreviewGallery(capturedImageData);
}

function showPreviewGallery(imageData) {
    const previewSection = document.getElementById("previewSection");
    const previewImage = document.getElementById("previewImage");
    
    // Hide camera controls and video, show preview
    document.getElementById("cameraControls").classList.add("hidden");
    video.style.display = "none";
    
    // Set preview image
    previewImage.src = imageData;
    previewSection.classList.remove("hidden");
}

function cancelCapture() {
    // Hide preview and show camera controls again
    document.getElementById("previewSection").classList.add("hidden");
    document.getElementById("cameraControls").classList.remove("hidden");
    
    capturedImageData = null;
    
    // Hide video initially, will be shown when camera starts
    video.style.display = "none";
    
    // Restart camera
    startCamera();
}

function openCropper() {
    if (!capturedImageData) {
        alert("No image captured.");
        return;
    }
    
    const cropperImage = document.getElementById("cropperImage");
    cropperImage.src = capturedImageData;
    
    const modal = document.getElementById("cropperModal");
    modal.classList.remove("hidden");
    
    // Wait for image to load, then initialize cropper
    cropperImage.onload = function() {
        // Destroy previous cropper if exists
        if (cropper) {
            cropper.destroy();
        }
        
        // Force container to have proper dimensions before initializing
        const canvas = cropperImage.parentElement;
        canvas.style.width = "100%";
        canvas.style.height = "450px";  // Larger height for full crop area expansion
        canvas.style.pointerEvents = "auto"; // Ensure pointer events are enabled
        
        // Initialize Cropper.js with professional mobile cropper settings
        cropper = new Cropper(cropperImage, {
            viewMode: 0,                    // Show full image, allow crop larger than container
            dragMode: 'move',               // Move image to position, then click edges to resize
            autoCropArea: 0.9,              // 90% of image area for initial crop
            guides: true,                   // Show rule of thirds grid lines
            center: true,                   // Show center indicator
            highlight: true,                // Highlight crop area
            cropBoxMovable: true,           // Allow moving crop box
            cropBoxResizable: true,         // Allow resizing crop box
            movable: true,                  // Allow moving the image inside container
            zoomable: true,                 // Enable zooming with wheel
            zoomOnWheel: true,              // Zoom on mouse wheel
            zoomOnTouch: true,              // Zoom on touch devices
            rotatable: false,               // Disable rotation
            scalable: false,                // Disable flipping/scaling
            toggleDragModeOnDblclick: false, // Disable double-click mode toggle
            modal: true,                    // Show dimmed background outside crop
            background: false,              // Hide container background grid
            aspectRatio: NaN,               // Free aspect ratio for flexible cropping
            responsive: true,               // Responsive to container changes
            minContainerHeight: 200,        // Minimum container height
            minContainerWidth: 200,         // Minimum container width
            minCanvasHeight: 50,            // Minimum canvas height
            minCanvasWidth: 50,             // Minimum canvas width
            minCropBoxHeight: 30,           // Minimum crop box size - small to allow expansion
            minCropBoxWidth: 30,            // Minimum crop box width
        });
    };
}

function cropAndSubmit() {
    if (!cropper) {
        alert("Cropper not initialized.");
        return;
    }
    
    // Get the cropped canvas with better quality
    const canvas = cropper.getCroppedCanvas({
        maxWidth: 512,
        maxHeight: 512,
        fillColor: '#fff',
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high',
    });
    
    // Convert canvas to base64
    croppedImageData = canvas.toDataURL("image/jpeg", 0.9);
    
    // Hide cropper modal
    document.getElementById("cropperModal").classList.add("hidden");
    
    // Destroy cropper
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
    
    // Show the cropped result preview
    showCroppedResultPreview();
}

function skipCropAndAnalyze() {
    if (!capturedImageData) {
        alert("No image captured.");
        return;
    }
    
    // Send original image without cropping
    document.getElementById("image_data").value = capturedImageData;
    
    // Hide preview section
    document.getElementById("previewSection").classList.add("hidden");
    
    // Submit form
    document.getElementById("captureForm").submit();
}

function cancelCrop() {
    // Hide cropper modal
    document.getElementById("cropperModal").classList.add("hidden");
    
    // Show preview section again
    document.getElementById("previewSection").classList.remove("hidden");
    
    // Destroy cropper
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
}

function showCroppedResultPreview() {
    // Hide preview section
    document.getElementById("previewSection").classList.add("hidden");
    
    // Show cropped result section
    document.getElementById("croppedResultSection").classList.remove("hidden");
    
    // Display the original and cropped images for comparison
    document.getElementById("originalComparisonImage").src = capturedImageData;
    document.getElementById("croppedComparisonImage").src = croppedImageData;
}

function acceptCroppedImage() {
    if (!croppedImageData) {
        alert("No cropped image data.");
        return;
    }
    
    // Set the image_data field with cropped image
    document.getElementById("image_data").value = croppedImageData;
    
    // Hide cropped result section
    document.getElementById("croppedResultSection").classList.add("hidden");
    
    // Submit form with cropped image
    document.getElementById("captureForm").submit();
}

function reCropImage() {
    // Hide cropped result section
    document.getElementById("croppedResultSection").classList.add("hidden");
    
    // Show preview section with cropper option
    document.getElementById("previewSection").classList.remove("hidden");
    
    // Open cropper again with the original image
    openCropper();
}

function toggleTheme() {
    document.body.classList.toggle("dark");
    document.body.classList.toggle("light");
}

function showLoader() {
    document.getElementById("loader").classList.remove("hidden");
}

// ========== INITIALIZATION ==========

// Hide video element initially - only show when camera is active
video.style.display = "none";

// ========== UPLOAD SECTION ENHANCEMENTS ==========

// Handle file input change - display selected file name
document.addEventListener("DOMContentLoaded", function() {
    // File selection indicator
    const selectedFileDisplay = document.getElementById("selectedFileName");
    
    if (fileInput && selectedFileDisplay) {
        fileInput.addEventListener("change", function() {
            if (this.files && this.files.length > 0) {
                const fileName = this.files[0].name;
                selectedFileDisplay.textContent = "✓ Selected file: " + fileName;
            } else {
                selectedFileDisplay.textContent = "";
            }
        });
    }
    
    // Show loading indicator when upload form is submitted
    const uploadForm = document.getElementById("uploadForm");
    const uploadLoading = document.getElementById("uploadLoading");
    
    if (uploadForm && uploadLoading) {
        uploadForm.addEventListener("submit", function() {
            uploadLoading.classList.remove("hidden");
        });
    }
    
    // Hide loading indicator when page loads (in case it's shown)
    if (uploadLoading) {
        uploadLoading.classList.add("hidden");
    }
});