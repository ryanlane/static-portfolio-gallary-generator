from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import shutil
from PIL import Image
import exifread
import json
import io
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
