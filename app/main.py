from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import shutil
from PIL import Image
import exifread
import json
import io
import zipfile
import tempfile
from datetime import datetime
from typing import List

app = FastAPI()

# Custom Jinja2 filter to parse JSON
def from_json(value):
    try:
        return json.loads(value) if value else {}
    except:
        return {}

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')
templates.env.filters['from_json'] = from_json

DB_PATH = 'gallery.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event('startup')
def startup():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS galleries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        featured_image_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gallery_id INTEGER,
        filename TEXT,
        title TEXT,
        description TEXT,
        camera_type TEXT,
        lens TEXT,
        settings TEXT,
        exif TEXT,
        enabled INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY(gallery_id) REFERENCES galleries(id)
    )''')
    
    # Add sort_order column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE images ADD COLUMN sort_order INTEGER DEFAULT 0')
    except:
        pass  # Column already exists
    
    conn.commit()
    conn.close()

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    conn = get_db()
    galleries = conn.execute('SELECT * FROM galleries').fetchall()
    # Get featured images for each gallery
    featured_images = {}
    for gallery in galleries:
        if gallery['featured_image_id']:
            img = conn.execute('SELECT * FROM images WHERE id=?', (gallery['featured_image_id'],)).fetchone()
            if img:
                featured_images[gallery['id']] = img
    conn.close()
    return templates.TemplateResponse('index.html', {'request': request, 'galleries': galleries, 'featured_images': featured_images})

@app.get('/gallery/{gallery_id}', response_class=HTMLResponse)
def view_gallery(request: Request, gallery_id: int):
    conn = get_db()
    gallery = conn.execute('SELECT * FROM galleries WHERE id=?', (gallery_id,)).fetchone()
    images = conn.execute('SELECT * FROM images WHERE gallery_id=? ORDER BY sort_order ASC, id ASC', (gallery_id,)).fetchall()
    conn.close()
    return templates.TemplateResponse('gallery.html', {'request': request, 'gallery': gallery, 'images': images})

@app.get('/create-gallery', response_class=HTMLResponse)
def create_gallery_form(request: Request):
    return templates.TemplateResponse('create_gallery.html', {'request': request})

@app.post('/create-gallery')
def create_gallery(title: str = Form(...), description: str = Form(None)):
    conn = get_db()
    conn.execute('INSERT INTO galleries (title, description) VALUES (?, ?)', (title, description))
    conn.commit()
    conn.close()
    return RedirectResponse('/', status_code=303)

# Gallery CRUD operations
@app.get('/galleries', response_class=HTMLResponse)
def list_galleries(request: Request):
    """List all galleries with management options"""
    conn = get_db()
    c = conn.cursor()
    galleries = c.execute('SELECT * FROM galleries ORDER BY id DESC').fetchall()
    
    # Get image counts and featured images for each gallery
    galleries_with_info = []
    for gallery in galleries:
        image_count = c.execute('SELECT COUNT(*) as count FROM images WHERE gallery_id=?', (gallery['id'],)).fetchone()['count']
        enabled_count = c.execute('SELECT COUNT(*) as count FROM images WHERE gallery_id=? AND enabled=1', (gallery['id'],)).fetchone()['count']
        
        featured_image = None
        if gallery['featured_image_id']:
            featured_image = c.execute('SELECT filename FROM images WHERE id=?', (gallery['featured_image_id'],)).fetchone()
        
        galleries_with_info.append({
            'id': gallery['id'],
            'title': gallery['title'],
            'description': gallery['description'],
            'featured_image_id': gallery['featured_image_id'],
            'image_count': image_count,
            'enabled_count': enabled_count,
            'featured_image': featured_image
        })
    
    conn.close()
    return templates.TemplateResponse('galleries_list.html', {
        'request': request, 
        'galleries': galleries_with_info
    })

@app.get('/gallery/{gallery_id}/edit', response_class=HTMLResponse)
def edit_gallery_form(request: Request, gallery_id: int):
    """Show gallery edit form"""
    conn = get_db()
    gallery = conn.execute('SELECT * FROM galleries WHERE id=?', (gallery_id,)).fetchone()
    conn.close()
    
    if not gallery:
        return RedirectResponse('/galleries?error=Gallery+not+found', status_code=303)
    
    return templates.TemplateResponse('edit_gallery.html', {
        'request': request, 
        'gallery': gallery
    })

@app.post('/gallery/{gallery_id}/update')
def update_gallery(gallery_id: int, title: str = Form(...), description: str = Form("")):
    """Update gallery details"""
    conn = get_db()
    c = conn.cursor()
    
    # Check if gallery exists
    gallery = c.execute('SELECT * FROM galleries WHERE id=?', (gallery_id,)).fetchone()
    if not gallery:
        conn.close()
        return RedirectResponse('/galleries?error=Gallery+not+found', status_code=303)
    
    # Update gallery
    c.execute('UPDATE galleries SET title=?, description=? WHERE id=?', (title, description, gallery_id))
    conn.commit()
    conn.close()
    
    return RedirectResponse(f'/gallery/{gallery_id}?message=Gallery+updated+successfully', status_code=303)

@app.post('/gallery/{gallery_id}/delete')
def delete_gallery(gallery_id: int):
    """Delete gallery and all its images"""
    conn = get_db()
    c = conn.cursor()
    
    # Check if gallery exists
    gallery = c.execute('SELECT * FROM galleries WHERE id=?', (gallery_id,)).fetchone()
    if not gallery:
        conn.close()
        return RedirectResponse('/galleries?error=Gallery+not+found', status_code=303)
    
    # Get all images in this gallery for file cleanup
    images = c.execute('SELECT filename FROM images WHERE gallery_id=?', (gallery_id,)).fetchall()
    
    # Delete images from database
    c.execute('DELETE FROM images WHERE gallery_id=?', (gallery_id,))
    
    # Delete gallery from database
    c.execute('DELETE FROM galleries WHERE id=?', (gallery_id,))
    
    conn.commit()
    conn.close()
    
    # Clean up image files
    gallery_dir = f'static/gallery_{gallery_id}'
    if os.path.exists(gallery_dir):
        shutil.rmtree(gallery_dir)
    
    # Clean up thumbnail files
    for image in images:
        thumb_path = f'static/thumbs/{image["filename"]}'
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
    
    return RedirectResponse('/galleries?message=Gallery+deleted+successfully', status_code=303)

@app.get('/gallery/{gallery_id}/add-image', response_class=HTMLResponse)
def add_image_form(request: Request, gallery_id: int):
    return templates.TemplateResponse('add_image.html', {'request': request, 'gallery_id': gallery_id})

@app.post('/gallery/{gallery_id}/add-image')
def add_image(gallery_id: int, file: UploadFile = File(...), title: str = Form(None), description: str = Form(None), camera_type: str = Form(None), lens: str = Form(None), settings: str = Form(None)):
    # Save image
    os.makedirs(f'static/gallery_{gallery_id}', exist_ok=True)
    os.makedirs('static/thumbs', exist_ok=True)
    file_path = f'static/gallery_{gallery_id}/{file.filename}'
    thumb_path = f'static/thumbs/{file.filename}'
    with open(file_path, 'wb') as f:
        content = file.file.read()
        f.write(content)
    # Generate thumbnail
    try:
        with Image.open(file_path) as img:
            img.thumbnail((400, 400))
            img.save(thumb_path)
    except Exception as e:
        print(f"Thumbnail error: {e}")
    # Extract EXIF (to be implemented)
    exif = ''
    # Save to DB
    conn = get_db()
    cur = conn.cursor()
    
    # Get next sort order
    max_sort = cur.execute('SELECT COALESCE(MAX(sort_order), -1) FROM images WHERE gallery_id=?', (gallery_id,)).fetchone()[0]
    next_sort_order = max_sort + 1
    
    cur.execute('''INSERT INTO images (gallery_id, filename, title, description, camera_type, lens, settings, exif, enabled, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (gallery_id, file.filename, title, description, camera_type, lens, settings, exif, 1, next_sort_order))
    image_id = cur.lastrowid
    # If this is the first image in the gallery, set as featured
    gallery = cur.execute('SELECT * FROM galleries WHERE id=?', (gallery_id,)).fetchone()
    if not gallery['featured_image_id']:
        cur.execute('UPDATE galleries SET featured_image_id=? WHERE id=?', (image_id, gallery_id))
    conn.commit()
    conn.close()
    return RedirectResponse(f'/gallery/{gallery_id}', status_code=303)

# Multiple image upload with EXIF extraction
@app.post('/gallery/{gallery_id}/upload-multiple')
def upload_multiple_images(gallery_id: int, files: List[UploadFile] = File(...)):
    results = []
    conn = get_db()
    cur = conn.cursor()
    
    for file in files:
        try:
            # Save image
            os.makedirs(f'static/gallery_{gallery_id}', exist_ok=True)
            os.makedirs('static/thumbs', exist_ok=True)
            file_path = f'static/gallery_{gallery_id}/{file.filename}'
            thumb_path = f'static/thumbs/{file.filename}'
            
            # Read file content
            content = file.file.read()
            
            # Extract EXIF data from original file content first
            exif_data = {}
            camera_type = ""
            lens = ""
            settings = ""
            
            try:
                # Create a BytesIO object from the content for EXIF reading
                content_stream = io.BytesIO(content)
                tags = exifread.process_file(content_stream)
                
                # Extract useful EXIF data
                if 'Image Make' in tags and 'Image Model' in tags:
                    camera_type = f"{tags['Image Make']} {tags['Image Model']}"
                elif 'Image Model' in tags:
                    camera_type = str(tags['Image Model'])
                
                if 'EXIF LensModel' in tags:
                    lens = str(tags['EXIF LensModel'])
                elif 'EXIF LensMake' in tags:
                    lens = str(tags['EXIF LensMake'])
                
                # Camera settings
                settings_parts = []
                if 'EXIF ExposureTime' in tags:
                    settings_parts.append(f"1/{int(1/float(tags['EXIF ExposureTime'].values[0]))}s")
                if 'EXIF FNumber' in tags:
                    settings_parts.append(f"f/{float(tags['EXIF FNumber'].values[0])}")
                if 'EXIF ISOSpeedRatings' in tags:
                    settings_parts.append(f"ISO {tags['EXIF ISOSpeedRatings']}")
                if 'EXIF FocalLength' in tags:
                    settings_parts.append(f"{float(tags['EXIF FocalLength'].values[0])}mm")
                
                settings = ", ".join(settings_parts)
                
                # Store full EXIF as JSON
                exif_data = {str(k): str(v) for k, v in tags.items() if k not in ['JPEGThumbnail', 'TIFFThumbnail']}
                
            except Exception as e:
                print(f"EXIF extraction error: {e}")
            
            # Now save the original file
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Generate thumbnail from the saved original file
            try:
                with Image.open(file_path) as img:
                    img.thumbnail((400, 400))
                    img.save(thumb_path)
            except Exception as e:
                print(f"Thumbnail error: {e}")
            
            # Get next sort order
            max_sort = cur.execute('SELECT COALESCE(MAX(sort_order), -1) FROM images WHERE gallery_id=?', (gallery_id,)).fetchone()[0]
            next_sort_order = max_sort + 1
            
            # Save to DB
            cur.execute('''INSERT INTO images (gallery_id, filename, title, description, camera_type, lens, settings, exif, enabled, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (gallery_id, file.filename, file.filename, "", camera_type, lens, settings, json.dumps(exif_data), 1, next_sort_order))
            image_id = cur.lastrowid
            
            # If this is the first image in the gallery, set as featured
            gallery = cur.execute('SELECT * FROM galleries WHERE id=?', (gallery_id,)).fetchone()
            if not gallery['featured_image_id']:
                cur.execute('UPDATE galleries SET featured_image_id=? WHERE id=?', (image_id, gallery_id))
            
            results.append({
                "success": True,
                "filename": file.filename,
                "image_id": image_id,
                "camera_type": camera_type,
                "lens": lens,
                "settings": settings
            })
            
        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e)
            })
    
    conn.commit()
    conn.close()
    return {"results": results}

# Set featured image for gallery
@app.post('/gallery/{gallery_id}/set-featured/{image_id}')
def set_featured_image(gallery_id: int, image_id: int):
    conn = get_db()
    cur = conn.cursor()
    
    # Verify the image belongs to this gallery
    image = cur.execute('SELECT * FROM images WHERE id=? AND gallery_id=?', (image_id, gallery_id)).fetchone()
    if not image:
        conn.close()
        return {"success": False, "error": "Image not found"}
    
    # Update gallery featured image
    cur.execute('UPDATE galleries SET featured_image_id=? WHERE id=?', (image_id, gallery_id))
    conn.commit()
    conn.close()
    
    return {"success": True}

# Remove featured image for gallery
@app.post('/gallery/{gallery_id}/remove-featured')
def remove_featured_image(gallery_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE galleries SET featured_image_id=NULL WHERE id=?', (gallery_id,))
    conn.commit()
    conn.close()
    return {"success": True}

# Reorder images in gallery
@app.post('/gallery/{gallery_id}/reorder')
async def reorder_images(gallery_id: int, request: Request):
    # Get the JSON body
    body = await request.body()
    try:
        data = json.loads(body.decode())
        image_order = data.get('image_order', [])
    except:
        return {"success": False, "error": "Invalid JSON"}
    
    conn = get_db()
    cur = conn.cursor()
    
    # Update sort_order for each image
    for item in image_order:
        image_id = item.get('id')
        sort_order = item.get('sort_order')
        
        # Verify the image belongs to this gallery
        image = cur.execute('SELECT * FROM images WHERE id=? AND gallery_id=?', (image_id, gallery_id)).fetchone()
        if image:
            cur.execute('UPDATE images SET sort_order=? WHERE id=?', (sort_order, image_id))
    
    conn.commit()
    conn.close()
    
    return {"success": True}

# Toggle image enabled/disabled
@app.post('/image/{image_id}/toggle-enabled')
def toggle_image_enabled(image_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT enabled, gallery_id FROM images WHERE id=?', (image_id,))
    row = cur.fetchone()
    if row:
        new_enabled = 0 if row['enabled'] else 1
        cur.execute('UPDATE images SET enabled=? WHERE id=?', (new_enabled, image_id))
        conn.commit()
        gallery_id = row['gallery_id']
        conn.close()
        return {"success": True, "enabled": bool(new_enabled)}
    else:
        conn.close()
        return {"success": False}

# Update image metadata
@app.post('/image/{image_id}/update')
def update_image(image_id: int, title: str = Form(None), description: str = Form(None), camera_type: str = Form(None), lens: str = Form(None), settings: str = Form(None)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE images SET title=?, description=?, camera_type=?, lens=?, settings=? WHERE id=?',
                (title, description, camera_type, lens, settings, image_id))
    conn.commit()
    conn.close()
    return {"success": True}

# Delete image
@app.post('/image/{image_id}/delete')
def delete_image(image_id: int):
    conn = get_db()
    cur = conn.cursor()
    # Get image info before deleting
    image = cur.execute('SELECT filename, gallery_id FROM images WHERE id=?', (image_id,)).fetchone()
    if image:
        gallery_id = image['gallery_id']
        filename = image['filename']
        
        # Delete from database
        cur.execute('DELETE FROM images WHERE id=?', (image_id,))
        
        # Remove featured image reference if this was the featured image
        cur.execute('UPDATE galleries SET featured_image_id=NULL WHERE featured_image_id=?', (image_id,))
        
        conn.commit()
        conn.close()
        
        # Delete files
        try:
            os.remove(f'static/gallery_{gallery_id}/{filename}')
            os.remove(f'static/thumbs/{filename}')
        except:
            pass  # Files might not exist
            
        return {"success": True, "gallery_id": gallery_id}
    else:
        conn.close()
        return {"success": False}

# Settings page
@app.get('/settings', response_class=HTMLResponse)
def settings(request: Request, message: str = None):
    return templates.TemplateResponse('settings.html', {'request': request, 'message': message})

# Reset database and static/gallery folders
@app.post('/settings/reset', response_class=HTMLResponse)
def reset_database(request: Request):
    # Remove DB file
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    # Remove all gallery folders
    static_dir = 'static'
    for name in os.listdir(static_dir):
        path = os.path.join(static_dir, name)
        if name.startswith('gallery_') and os.path.isdir(path):
            shutil.rmtree(path)
    # Remove all thumbs
    thumbs_dir = os.path.join(static_dir, 'thumbs')
    if os.path.isdir(thumbs_dir):
        for f in os.listdir(thumbs_dir):
            os.remove(os.path.join(thumbs_dir, f))
    # Recreate DB tables
    startup()
    return RedirectResponse('/settings?message=Database+reset+successfully', status_code=303)

# Static Site Generation Routes
@app.get('/generate', response_class=HTMLResponse)
def generate_page(request: Request):
    """Show static site generation options"""
    conn = get_db()
    c = conn.cursor()
    galleries = c.execute('SELECT * FROM galleries ORDER BY id').fetchall()
    
    # Get featured images for each gallery (similar to galleries list)
    galleries_with_info = []
    for gallery in galleries:
        featured_image = None
        if gallery['featured_image_id']:
            featured_image = c.execute('SELECT filename FROM images WHERE id=?', (gallery['featured_image_id'],)).fetchone()
        
        galleries_with_info.append({
            'id': gallery['id'],
            'title': gallery['title'],
            'description': gallery['description'],
            'featured_image_id': gallery['featured_image_id'],
            'featured_image': featured_image
        })
    
    conn.close()
    
    # Get available themes
    themes = []
    static_templates_dir = 'static_templates'
    if os.path.exists(static_templates_dir):
        for theme_name in os.listdir(static_templates_dir):
            theme_path = os.path.join(static_templates_dir, theme_name)
            if os.path.isdir(theme_path) and os.path.exists(os.path.join(theme_path, 'index.html')):
                themes.append({
                    'name': theme_name,
                    'title': theme_name.replace('_', ' ').title()
                })
    
    return templates.TemplateResponse('generate.html', {
        'request': request,
        'galleries': galleries_with_info,
        'themes': themes
    })

@app.post('/generate/static')
def generate_static_site(
    site_title: str = Form("My Photo Gallery"),
    site_description: str = Form(""),
    theme: str = Form("minimal"),
    gallery_ids: List[str] = Form([])
):
    """Generate static site with selected galleries and theme"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get selected galleries with their images
        galleries = []
        for gallery_id in gallery_ids:
            gallery = c.execute('SELECT * FROM galleries WHERE id=?', (gallery_id,)).fetchone()
            if gallery:
                images = c.execute('''
                    SELECT * FROM images 
                    WHERE gallery_id=? AND enabled=1 
                    ORDER BY sort_order ASC
                ''', (gallery_id,)).fetchall()
                
                galleries.append({
                    'id': gallery['id'],
                    'title': gallery['title'],
                    'description': gallery['description'],
                    'images': [dict(img) for img in images]
                })
        
        conn.close()
        
        if not galleries:
            return RedirectResponse('/generate?error=No+galleries+selected', status_code=303)
        
        # Create temporary directory for static site
        temp_dir = tempfile.mkdtemp(prefix='static_site_')
        
        try:
            # Create directory structure
            images_dir = os.path.join(temp_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # Copy selected images
            for gallery in galleries:
                for image in gallery['images']:
                    src_path = os.path.join('static', f'gallery_{gallery["id"]}', image['filename'])
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, os.path.join(images_dir, image['filename']))
            
            # Load and render template
            theme_template_path = os.path.join('static_templates', theme, 'index.html')
            if not os.path.exists(theme_template_path):
                theme_template_path = os.path.join('static_templates', 'minimal', 'index.html')
            
            with open(theme_template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Simple template rendering (we'll use Jinja2 properly)
            from jinja2 import Environment, FileSystemLoader
            
            env = Environment(loader=FileSystemLoader('static_templates'))
            env.filters['from_json'] = from_json
            
            template = env.get_template(f'{theme}/index.html')
            
            rendered_html = template.render(
                site_title=site_title,
                site_description=site_description,
                galleries=galleries
            )
            
            # Write HTML file
            with open(os.path.join(temp_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            
            # Create ZIP file
            zip_path = os.path.join('static', 'generated_sites', f'site_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip')
            os.makedirs(os.path.dirname(zip_path), exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            # Return download link
            return RedirectResponse(f'/generate?success=Site+generated+successfully&download={os.path.basename(zip_path)}', status_code=303)
            
        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        return RedirectResponse(f'/generate?error=Generation+failed:+{str(e)}', status_code=303)

@app.get('/download/{filename}')
def download_generated_site(filename: str):
    """Download generated static site"""
    file_path = os.path.join('static', 'generated_sites', filename)
    if os.path.exists(file_path) and filename.endswith('.zip'):
        return FileResponse(
            file_path,
            media_type='application/zip',
            filename=filename
        )
    return RedirectResponse('/generate?error=File+not+found', status_code=303)

@app.get('/preview/{theme}')
def preview_theme(theme: str, request: Request):
    """Preview a theme with sample data"""
    # Sample gallery data for preview
    sample_galleries = [{
        'id': 1,
        'title': 'Sample Gallery',
        'description': 'This is a sample gallery to preview the theme.',
        'images': [
            {
                'filename': 'sample1.jpg',
                'title': 'Sample Image 1',
                'description': 'A beautiful landscape photograph.',
                'camera_type': 'Canon EOS R5',
                'lens': 'RF 24-70mm f/2.8L',
                'settings': 'f/8, 1/125s, ISO 100',
                'enabled': 1
            },
            {
                'filename': 'sample2.jpg',
                'title': 'Sample Image 2',
                'description': 'Portrait with shallow depth of field.',
                'camera_type': 'Sony A7R IV',
                'lens': '85mm f/1.4 GM',
                'settings': 'f/1.4, 1/200s, ISO 400',
                'enabled': 1
            }
        ]
    }]
    
    try:
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader('static_templates'))
        env.filters['from_json'] = from_json
        
        template = env.get_template(f'{theme}/index.html')
        rendered_html = template.render(
            site_title="Theme Preview",
            site_description="This is a preview of the selected theme with sample content.",
            galleries=sample_galleries
        )
        
        return HTMLResponse(content=rendered_html)
        
    except Exception as e:
        return HTMLResponse(f"<h1>Preview Error</h1><p>Could not load theme '{theme}': {str(e)}</p>")
