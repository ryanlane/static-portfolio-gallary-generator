document.addEventListener('DOMContentLoaded', function() {
  let draggedElement = null;
  
  // Drag and drop functionality
  document.addEventListener('dragstart', function(e) {
    if (e.target.classList.contains('card')) {
      draggedElement = e.target;
      e.target.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/html', e.target.outerHTML);
    }
  });

  document.addEventListener('dragend', function(e) {
    if (e.target.classList.contains('card')) {
      e.target.classList.remove('dragging');
      draggedElement = null;
    }
  });

  document.addEventListener('dragover', function(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    if (e.target.closest('.card') && draggedElement) {
      const targetCard = e.target.closest('.card');
      if (targetCard !== draggedElement) {
        targetCard.classList.add('drag-over');
      }
    }
  });

  document.addEventListener('dragleave', function(e) {
    if (e.target.classList.contains('card')) {
      e.target.classList.remove('drag-over');
    }
  });

  document.addEventListener('drop', function(e) {
    e.preventDefault();
    
    const targetCard = e.target.closest('.card');
    if (targetCard && draggedElement && targetCard !== draggedElement) {
      targetCard.classList.remove('drag-over');
      
      // Get the gallery container
      const gallery = document.querySelector('.gallery-flex');
      const cards = Array.from(gallery.children);
      
      // Find positions
      const draggedIndex = cards.indexOf(draggedElement);
      const targetIndex = cards.indexOf(targetCard);
      
      // Reorder DOM elements
      if (draggedIndex < targetIndex) {
        targetCard.parentNode.insertBefore(draggedElement, targetCard.nextSibling);
      } else {
        targetCard.parentNode.insertBefore(draggedElement, targetCard);
      }
      
      // Update sort order in database
      updateImageOrder(gallery);
    }
  });

  // Function to update image order in database
  function updateImageOrder(gallery) {
    const cards = Array.from(gallery.children);
    const imageOrder = cards.map((card, index) => ({
      id: parseInt(card.getAttribute('data-id')),
      sort_order: index
    }));
    
    const galleryId = cards[0]?.getAttribute('data-gallery-id');
    if (galleryId) {
      fetch(`/gallery/${galleryId}/reorder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({ image_order: imageOrder })
      }).then(resp => {
        if (!resp.ok) {
          console.error('Failed to update image order');
          // Optionally reload the page on error
          // window.location.reload();
        }
      }).catch(err => {
        console.error('Error updating image order:', err);
      });
    }
  }
  // Use event delegation for all buttons
  document.addEventListener('click', function(e) {
    // Toggle enabled/disabled
    if (e.target.classList.contains('toggle-enabled')) {
      e.preventDefault();
      const btn = e.target;
      const imageId = btn.getAttribute('data-id');
      const card = document.getElementById(`img-${imageId}`);
      
      fetch(`/image/${imageId}/toggle-enabled`, {
        method: 'POST',
        headers: { 'accept': 'application/json' }
      }).then(resp => {
        if (resp.ok) {
          const isCurrentlyEnabled = btn.getAttribute('aria-pressed') === 'true';
          const newEnabled = !isCurrentlyEnabled;
          
          btn.textContent = newEnabled ? 'Disable' : 'Enable';
          btn.setAttribute('aria-pressed', newEnabled ? 'true' : 'false');
          
          if (newEnabled) {
            card.classList.remove('is-disabled');
          } else {
            card.classList.add('is-disabled');
          }
        } else {
          window.location.reload();
        }
      }).catch(() => {
        window.location.reload();
      });
    }

    // Edit image metadata
    if (e.target.classList.contains('edit-image')) {
      e.preventDefault();
      const btn = e.target;
      const imageId = btn.getAttribute('data-id');
      const titleDisplay = document.getElementById(`title-display-${imageId}`);
      const titleEdit = document.getElementById(`title-edit-${imageId}`);
      const descDisplay = document.getElementById(`desc-display-${imageId}`);
      
      if (titleEdit.style.display === 'none' || titleEdit.style.display === '') {
        titleDisplay.style.display = 'none';
        titleEdit.style.display = 'block';
        if (descDisplay) descDisplay.style.display = 'none';
        btn.textContent = '❌';
      } else {
        titleDisplay.style.display = 'block';
        titleEdit.style.display = 'none';
        if (descDisplay) descDisplay.style.display = 'block';
        btn.textContent = '✏️';
      }
    }

    // Save edit
    if (e.target.classList.contains('save-edit')) {
      e.preventDefault();
      const btn = e.target;
      const imageId = btn.getAttribute('data-id');
      const title = document.getElementById(`title-input-${imageId}`).value;
      const description = document.getElementById(`desc-input-${imageId}`).value;
      const camera = document.getElementById(`camera-input-${imageId}`).value;
      const lens = document.getElementById(`lens-input-${imageId}`).value;
      const settings = document.getElementById(`settings-input-${imageId}`).value;

      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', description);
      formData.append('camera_type', camera);
      formData.append('lens', lens);
      formData.append('settings', settings);

      fetch(`/image/${imageId}/update`, {
        method: 'POST',
        body: formData
      }).then(resp => {
        if (resp.ok) {
          document.getElementById(`title-display-${imageId}`).textContent = title;
          const descDisplay = document.getElementById(`desc-display-${imageId}`);
          if (descDisplay) {
            descDisplay.textContent = description;
            descDisplay.style.display = description ? 'block' : 'none';
          }
          
          document.getElementById(`title-display-${imageId}`).style.display = 'block';
          document.getElementById(`title-edit-${imageId}`).style.display = 'none';
          if (descDisplay) descDisplay.style.display = description ? 'block' : 'none';
          document.querySelector(`.edit-image[data-id="${imageId}"]`).textContent = '✏️';
        } else {
          alert('Failed to save changes');
        }
      });
    }

    // Cancel edit
    if (e.target.classList.contains('cancel-edit')) {
      e.preventDefault();
      const btn = e.target;
      const imageId = btn.getAttribute('data-id');
      
      document.getElementById(`title-display-${imageId}`).style.display = 'block';
      document.getElementById(`title-edit-${imageId}`).style.display = 'none';
      const descDisplay = document.getElementById(`desc-display-${imageId}`);
      if (descDisplay) descDisplay.style.display = 'block';
      document.querySelector(`.edit-image[data-id="${imageId}"]`).textContent = '✏️';
    }

    // Delete image
    if (e.target.classList.contains('delete-image')) {
      e.preventDefault();
      const btn = e.target;
      const imageId = btn.getAttribute('data-id');
      
      if (confirm('Are you sure you want to delete this image?')) {
        fetch(`/image/${imageId}/delete`, {
          method: 'POST',
          headers: { 'accept': 'application/json' }
        }).then(resp => resp.json()).then(data => {
          if (data.success) {
            document.getElementById(`img-${imageId}`).remove();
          } else {
            alert('Failed to delete image');
          }
        }).catch(() => {
          window.location.reload();
        });
      }
    }
    
    // Toggle EXIF data display
    if (e.target.classList.contains('exif-toggle')) {
      e.preventDefault();
      const btn = e.target;
      const imageId = btn.getAttribute('data-id');
      const exifData = document.getElementById(`exif-data-${imageId}`);
      
      if (exifData.style.display === 'none') {
        exifData.style.display = 'block';
        btn.textContent = '📊 Hide EXIF Data';
      } else {
        exifData.style.display = 'none';
        btn.textContent = '📊 EXIF Data';
      }
    }

    // Toggle featured image
    if (e.target.classList.contains('star-toggle')) {
      e.preventDefault();
      const btn = e.target;
      const imageId = btn.getAttribute('data-id');
      const galleryId = btn.getAttribute('data-gallery-id');
      const currentCard = document.getElementById(`img-${imageId}`);
      const isCurrentlyFeatured = currentCard.classList.contains('is-featured');
      
      // If clicking on already featured image, remove featured status
      if (isCurrentlyFeatured) {
        fetch(`/gallery/${galleryId}/remove-featured`, {
          method: 'POST',
          headers: { 'accept': 'application/json' }
        }).then(resp => resp.json()).then(data => {
          if (data.success) {
            // Remove featured styling from current card
            currentCard.classList.remove('is-featured');
            btn.textContent = '☆';
            btn.title = 'Set as featured';
          }
        }).catch(() => {
          alert('Error removing featured image');
        });
      } else {
        // Set this image as featured
        fetch(`/gallery/${galleryId}/set-featured/${imageId}`, {
          method: 'POST',
          headers: { 'accept': 'application/json' }
        }).then(resp => resp.json()).then(data => {
          if (data.success) {
            // Remove featured styling from all cards
            document.querySelectorAll('.card').forEach(card => {
              card.classList.remove('is-featured');
            });
            
            // Update all star buttons
            document.querySelectorAll('.star-toggle').forEach(starBtn => {
              starBtn.textContent = '☆';
              starBtn.title = 'Set as featured';
            });
            
            // Add featured styling to current card
            currentCard.classList.add('is-featured');
            
            // Update current star button
            btn.textContent = '⭐';
            btn.title = 'Remove as featured';
          } else {
            alert('Failed to set featured image');
          }
        }).catch(() => {
          alert('Error setting featured image');
        });
      }
    }
  });
});
