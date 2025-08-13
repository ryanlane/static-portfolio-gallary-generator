# Template Creation Examples

This file contains examples of common template patterns you can use in your own templates.

## 1. Different Grid Layouts

### Masonry-style (Pinterest-like)
```css
.image-grid {
    column-count: 4;
    column-gap: 20px;
}

.image-item {
    break-inside: avoid;
    margin-bottom: 20px;
}
```

### Fixed Aspect Ratio Grid
```css
.image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.image-item {
    aspect-ratio: 16/9; /* Or 4/3, 1/1, etc. */
}
```

### Staggered Grid
```css
.image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 10px;
}

.image-item:nth-child(odd) {
    transform: translateY(20px);
}
```

## 2. Different Color Schemes

### Dark Theme
```css
body {
    background: #1a1a1a;
    color: #ffffff;
}

.gallery {
    background: #2d2d2d;
}

.gallery-header {
    background: #333333;
}
```

### Minimal White
```css
body {
    background: #ffffff;
    color: #333333;
}

.gallery {
    background: #ffffff;
    border: 1px solid #eeeeee;
}

.gallery-header {
    background: #f8f8f8;
    color: #333333;
}
```

### Colorful
```css
.gallery:nth-child(1) .gallery-header { background: #e74c3c; }
.gallery:nth-child(2) .gallery-header { background: #3498db; }
.gallery:nth-child(3) .gallery-header { background: #2ecc71; }
.gallery:nth-child(4) .gallery-header { background: #f39c12; }
.gallery:nth-child(5) .gallery-header { background: #9b59b6; }
```

## 3. Advanced Image Effects

### Parallax Effect
```css
.image-item {
    background-attachment: fixed;
    background-position: center;
    background-repeat: no-repeat;
    background-size: cover;
}
```

### Blur to Focus
```css
.image-item img {
    filter: blur(2px);
    transition: filter 0.3s ease;
}

.image-item:hover img {
    filter: blur(0);
}
```

### Black and White to Color
```css
.image-item img {
    filter: grayscale(100%);
    transition: filter 0.3s ease;
}

.image-item:hover img {
    filter: grayscale(0%);
}
```

## 4. Layout Variations

### Single Column Layout
```css
.image-grid {
    display: flex;
    flex-direction: column;
    max-width: 800px;
    margin: 0 auto;
}

.image-item {
    margin-bottom: 40px;
}
```

### Horizontal Scroll Gallery
```css
.image-grid {
    display: flex;
    overflow-x: auto;
    gap: 20px;
    padding-bottom: 20px;
}

.image-item {
    flex: 0 0 300px;
    height: 400px;
}
```

### Carousel Style
```css
.gallery {
    position: relative;
    overflow: hidden;
}

.image-grid {
    display: flex;
    transition: transform 0.3s ease;
}

.image-item {
    flex: 0 0 100%;
    max-width: 100%;
}
```

## 5. Typography Variations

### Large Headers
```css
.site-title {
    font-size: 4rem;
    font-weight: 100;
    letter-spacing: 2px;
}

.gallery-title {
    font-size: 3rem;
    font-weight: 300;
}
```

### Script Fonts
```css
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap');

.site-title {
    font-family: 'Dancing Script', cursive;
    font-size: 3.5rem;
}
```

### Minimalist Typography
```css
.site-title {
    font-weight: 300;
    font-size: 2rem;
    text-transform: uppercase;
    letter-spacing: 3px;
}
```

## 6. Interactive Features

### Image Zoom on Click
```javascript
document.querySelectorAll('.image-item img').forEach(img => {
    img.addEventListener('click', function() {
        this.classList.toggle('zoomed');
    });
});
```

```css
.image-item img.zoomed {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(1.5);
    z-index: 1000;
    max-width: 90vw;
    max-height: 90vh;
}
```

### Gallery Navigation
```javascript
let currentGallery = 0;
const galleries = document.querySelectorAll('.gallery');

function showGallery(index) {
    galleries.forEach((gallery, i) => {
        gallery.style.display = i === index ? 'block' : 'none';
    });
}

function nextGallery() {
    currentGallery = (currentGallery + 1) % galleries.length;
    showGallery(currentGallery);
}
```

### Filter by Metadata
```javascript
function filterByCamera(cameraType) {
    document.querySelectorAll('.image-item').forEach(item => {
        const meta = item.querySelector('.image-meta');
        if (!meta || !meta.textContent.includes(cameraType)) {
            item.style.display = 'none';
        } else {
            item.style.display = 'block';
        }
    });
}
```

## 7. Conditional Template Logic

### Show Different Layouts Based on Image Count
```html
{% if gallery.images|length > 12 %}
    <!-- Use masonry layout for many images -->
    <div class="image-grid masonry">
{% elif gallery.images|length > 4 %}
    <!-- Use regular grid for medium number of images -->
    <div class="image-grid regular">
{% else %}
    <!-- Use showcase layout for few images -->
    <div class="image-grid showcase">
{% endif %}
```

### Feature First Image
```html
{% for image in gallery.images %}
    {% if loop.first %}
        <div class="featured-image">
            <img src="galleries/{{ loop.index0 }}/{{ image.filename }}" alt="{{ image.title }}">
        </div>
    {% else %}
        <div class="thumbnail">
            <img src="galleries/{{ loop.index0 }}/{{ image.filename }}" alt="{{ image.title }}">
        </div>
    {% endif %}
{% endfor %}
```

### Group Images by Camera Type
```html
{% set cameras = gallery.images | groupby('camera_type') %}
{% for camera_type, images in cameras %}
    <h3>{{ camera_type or 'Unknown Camera' }}</h3>
    <div class="camera-group">
        {% for image in images %}
            <!-- Display images for this camera -->
        {% endfor %}
    </div>
{% endfor %}
```

## 8. Performance Optimizations

### Lazy Loading with Intersection Observer
```javascript
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            observer.unobserve(img);
        }
    });
});

document.querySelectorAll('img[data-src]').forEach(img => {
    imageObserver.observe(img);
});
```

### Progressive Image Loading
```html
<img src="galleries/{{ loop.index0 }}/thumb_{{ image.filename }}" 
     data-src="galleries/{{ loop.index0 }}/{{ image.filename }}" 
     class="lazy" 
     alt="{{ image.title }}">
```

Remember: These are just examples to inspire your own templates. Mix and match these patterns to create something unique!
