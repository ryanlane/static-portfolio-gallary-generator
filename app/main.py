from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

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
        description TEXT
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
        FOREIGN KEY(gallery_id) REFERENCES galleries(id)
    )''')
    conn.commit()
    conn.close()

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    conn = get_db()
    galleries = conn.execute('SELECT * FROM galleries').fetchall()
    conn.close()
    return templates.TemplateResponse('index.html', {'request': request, 'galleries': galleries})

@app.get('/gallery/{gallery_id}', response_class=HTMLResponse)
def view_gallery(request: Request, gallery_id: int):
    conn = get_db()
    gallery = conn.execute('SELECT * FROM galleries WHERE id=?', (gallery_id,)).fetchone()
    images = conn.execute('SELECT * FROM images WHERE gallery_id=?', (gallery_id,)).fetchall()
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
    file_path = f'static/gallery_{gallery_id}/{file.filename}'
    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    # Extract EXIF (to be implemented)
    exif = ''
    # Save to DB
    conn = get_db()
    conn.execute('''INSERT INTO images (gallery_id, filename, title, description, camera_type, lens, settings, exif) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (gallery_id, file.filename, title, description, camera_type, lens, settings, exif))
    conn.commit()
    conn.close()
    return RedirectResponse(f'/gallery/{gallery_id}', status_code=303)
