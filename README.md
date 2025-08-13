# Static Portfolio Gallery Generator

A web-based tool for creating and managing image galleries with EXIF data extraction and static site generation capabilities.

## Features

- 🖼️ **Multiple Image Upload** - Drag & drop or browse multiple images at once
- 📸 **EXIF Data Extraction** - Automatic extraction of camera, lens, and settings
- 🎯 **Gallery Management** - Create unlimited galleries with titles and descriptions
- ✏️ **Inline Editing** - Edit image metadata directly in the interface
- 🎨 **Thumbnail Generation** - Automatic thumbnail creation for fast loading
- 👁️ **Enable/Disable Images** - Control which images appear in published galleries
- 🌐 **Static Site Generation** - Export galleries as deployable HTML sites
- 📱 **Responsive Interface** - Works on desktop and mobile devices

## Quick Start

### Option 1: Automatic Installation
```bash
./install.sh
```

### Option 2: Manual Installation
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p static/thumbs templates/partials
```

## Running the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

## Usage

1. **Create a Gallery** - Click "Create New Gallery" and add a title/description
2. **Add Images** - Click "Add Image" and drag & drop multiple images
3. **Manage Images** - Edit titles, descriptions, camera info, and enable/disable images
4. **Generate Static Site** - Export your galleries for deployment (coming soon)

## Database Reset

To reset all galleries and images, visit http://localhost:8000/settings and click "Reset Image Database".

## Technology Stack

- **Backend**: FastAPI, SQLite, Uvicorn
- **Frontend**: Jinja2 templates, vanilla JavaScript
- **Image Processing**: Pillow (thumbnails), ExifRead (metadata)
- **Deployment**: Static HTML generation (coming soon)

## Development

The application uses:
- SQLite database for gallery and image metadata
- File system storage for images and thumbnails
- AJAX for real-time UI updates without page reloads
- Event delegation for dynamic JavaScript functionality
