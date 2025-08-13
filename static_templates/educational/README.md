# Educational Template Documentation

This is a **bare bones educational template** designed to help you learn how to create your own static gallery templates.

## 📚 What You'll Learn

This template demonstrates:

- **Jinja2 templating syntax** - How to use variables, loops, and conditionals
- **Responsive CSS Grid** - Modern layout techniques for image galleries
- **Template variables** - What data is available to your template
- **File structure** - How images are organized and referenced
- **Responsive design** - Making your gallery work on all devices
- **Interactive features** - Adding JavaScript for enhanced user experience

## 🗂️ Template Variables Available

When your template is rendered, you have access to these variables:

### Site-Level Variables
- `site_title` - The title of the entire website
- `site_description` - Optional description of the site

### Gallery Variables
- `galleries` - List of all gallery objects

### Gallery Object Properties
Each gallery in the `galleries` list contains:
- `title` - Gallery title
- `description` - Gallery description (optional)
- `images` - List of image objects in this gallery

### Image Object Properties
Each image contains:
- `filename` - The image filename (without path)
- `title` - Image title (optional)
- `description` - Image description (optional)
- `camera_type` - Camera used (optional)
- `lens` - Lens information (optional)
- `settings` - Camera settings (optional)

## 🎨 Customization Guide

### 1. Styling
All CSS is contained in the `<style>` section. You can:
- Change colors by modifying the color values
- Adjust the grid layout by changing `grid-template-columns`
- Modify spacing with padding and margin values
- Add your own animations and transitions

### 2. Layout
The template uses CSS Grid for layout:
```css
.image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 0;
}
```

- `auto-fit` - Automatically adjusts number of columns
- `minmax(250px, 1fr)` - Each column is at least 250px wide
- `gap: 0` - No space between images (change this for spacing)

### 3. Responsive Breakpoints
Mobile styles are defined in the media query:
```css
@media (max-width: 768px) {
    /* Mobile styles here */
}
```

### 4. Image Paths
Images are referenced using this pattern:
```html
<img src="galleries/{{ loop.index0 }}/{{ image.filename }}">
```

- `galleries/` - Base directory for all gallery images
- `{{ loop.index0 }}` - Gallery ID (0-based counter)
- `{{ image.filename }}` - Individual image filename

## 🔧 Template Syntax Examples

### Basic Variable Output
```html
<h1>{{ site_title or "Default Title" }}</h1>
```

### Conditional Rendering
```html
{% if gallery.description %}
<p>{{ gallery.description }}</p>
{% endif %}
```

### Loops
```html
{% for gallery in galleries %}
    <h2>{{ gallery.title }}</h2>
    {% for image in gallery.images %}
        <img src="galleries/{{ loop.index0 }}/{{ image.filename }}">
    {% endfor %}
{% endfor %}
```

### Loop Variables
Inside loops, you have access to:
- `loop.index` - Current iteration (1-based)
- `loop.index0` - Current iteration (0-based)
- `loop.first` - True if first iteration
- `loop.last` - True if last iteration

## 🚀 Advanced Features You Can Add

### 1. Lightbox
Add a proper lightbox library like Lightbox2 or create your own modal

### 2. Filtering
Add JavaScript to filter images by gallery or metadata

### 3. Lazy Loading
The template includes `loading="lazy"` on images for better performance

### 4. Image Optimization
Use responsive images with `srcset` for different screen sizes

### 5. Custom Animations
Add CSS animations for image loading and transitions

## 📁 File Structure

```
static_templates/educational/
└── index.html          # This template file

Generated site structure:
├── index.html          # Generated from your template
└── galleries/
    ├── 0/             # First gallery
    │   ├── image1.jpg
    │   └── image2.jpg
    ├── 1/             # Second gallery
    │   ├── image1.jpg
    │   └── image2.jpg
    └── ...
```

## 🎯 Getting Started

1. **Copy this template** to create your own
2. **Modify the CSS** to match your desired look
3. **Test with your galleries** using the generate function
4. **Add your own features** like lightboxes or filtering
5. **Share your template** with others!

## 💡 Tips for Creating Templates

1. **Start simple** - Begin with basic HTML and CSS, add features gradually
2. **Test responsive design** - Make sure it works on mobile devices
3. **Use semantic HTML** - Use proper headings, sections, and alt text
4. **Optimize performance** - Use lazy loading and efficient CSS
5. **Add accessibility** - Include proper ARIA labels and keyboard navigation
6. **Document your work** - Add comments explaining your customizations

## 🔗 Useful Resources

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [CSS Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Responsive Web Design](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)
- [Web Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

Happy template building! 🎨
