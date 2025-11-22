from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
import os
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# ==================== EMAIL CONFIG ====================
MINISTRY_EMAIL = os.environ.get("MINISTRY_EMAIL", "onyangoodhiambo49@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "getx qsmf zyxd ftxd")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# =====================================================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here-change-this")
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
PDF_FOLDER = os.path.join(UPLOAD_FOLDER, 'pdf')
DOCUMENT_FOLDER = os.path.join(UPLOAD_FOLDER, 'documents')
AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, 'audio')
VIDEO_FOLDER = os.path.join(UPLOAD_FOLDER, 'video')
IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')

for folder in [PDF_FOLDER, DOCUMENT_FOLDER, AUDIO_FOLDER, VIDEO_FOLDER, IMAGE_FOLDER]:
    os.makedirs(folder, exist_ok=True)

TESTIMONIES_FILE = os.path.join(BASE_DIR, 'testimonies.json')
PARTNERSHIPS_FILE = os.path.join(BASE_DIR, 'partnerships.json')

ALLOWED_EXTENSIONS = {
    'pdf': {'pdf'},
    'documents': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'odt', 'rtf'},
    'audio': {'mp3', 'wav', 'ogg', 'm4a', 'aac'},
    'video': {'mp4', 'webm', 'mov', 'avi', 'mkv'},
    'images': {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
}

def allowed_file(filename, file_type):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

def get_uploaded_files():
    files = {
        'pdf': sorted([f for f in os.listdir(PDF_FOLDER) if os.path.isfile(os.path.join(PDF_FOLDER, f))]),
        'documents': sorted([f for f in os.listdir(DOCUMENT_FOLDER) if os.path.isfile(os.path.join(DOCUMENT_FOLDER, f))]),
        'audio': sorted([f for f in os.listdir(AUDIO_FOLDER) if os.path.isfile(os.path.join(AUDIO_FOLDER, f))]),
        'video': sorted([f for f in os.listdir(VIDEO_FOLDER) if os.path.isfile(os.path.join(VIDEO_FOLDER, f))]),
        'images': sorted([f for f in os.listdir(IMAGE_FOLDER) if os.path.isfile(os.path.join(IMAGE_FOLDER, f))])
    }
    return files

def load_testimonies():
    if os.path.exists(TESTIMONIES_FILE):
        try:
            with open(TESTIMONIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_testimony(data):
    testimonies = load_testimonies()
    new_testimony = {
        "name": data.get('name', '').strip(),
        "role": data.get('role', 'Member').strip() or "Member",
        "message": data.get('message', '').strip(),
        "date": datetime.now().strftime("%B %Y")
    }
    testimonies.insert(0, new_testimony)
    with open(TESTIMONIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(testimonies, f, indent=2, ensure_ascii=False)

@app.context_processor
def inject_testimonies():
    return dict(get_testimonies=load_testimonies)

# ==================== UNIVERSAL EMAIL FUNCTION ====================
def send_email(subject, body):
    """Send email - DISABLED on Render to prevent crashes"""
    # Skip email completely on production
    print(f"📧 Email notification (saved to logs only): {subject}")
    print(f"📄 Body preview: {body[:200]}...")
    return True  # Return True to prevent any error handling

# ==================== PARTNERSHIP STORAGE ====================
def save_partnership(data):
    """Save partnership data to JSON file"""
    partnerships = []
    if os.path.exists(PARTNERSHIPS_FILE):
        try:
            with open(PARTNERSHIPS_FILE, 'r', encoding='utf-8') as f:
                partnerships = json.load(f)
        except:
            partnerships = []
    
    partnerships.insert(0, data)
    
    with open(PARTNERSHIPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(partnerships, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Partnership saved to {PARTNERSHIPS_FILE}")

# ==================== PUBLIC ROUTES ====================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/sermons")
def sermons():
    sermons_list = []
    folders = [
        (PDF_FOLDER, "pdf"),
        (DOCUMENT_FOLDER, "documents"),
        (AUDIO_FOLDER, "audio"),
        (VIDEO_FOLDER, "video"),
    ]
    for folder_path, file_type in folders:
        if not os.path.exists(folder_path):
            continue
        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath):
                timestamp = os.path.getmtime(filepath)
                uploaded_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                clean_title = os.path.splitext(filename)[0]
                clean_title = clean_title.replace('_', ' ').replace('-', ' ').title()
                sermons_list.append({
                    "title": clean_title,
                    "description": "",
                    "filename": filename,
                    "file_type": file_type,
                    "uploaded_at": uploaded_date,
                    "timestamp": timestamp
                })
    sermons_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return render_template("sermons.html", sermons=sermons_list)

@app.route("/learn-more")
def learn_more():
    return render_template("learn_more.html")

@app.route("/join-our-mission")
def join_our_mission():
    return render_template("join_our_mission.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/donate")
def donate():
    flash("Thank you for your heart to give! Use the Donate button on the Join page.", "info")
    return redirect(url_for("join_our_mission"))

# ==================== YOUTH MINISTRY ====================
YOUTH_DATA_FILE = os.path.join(BASE_DIR, "youth_ministry.json")

def load_youth_data():
    if os.path.exists(YOUTH_DATA_FILE):
        try:
            with open(YOUTH_DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"leaders": [], "events": []}

def save_youth_data(data):
    with open(YOUTH_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/admin-youth-ministry")
def admin_youth_ministry():
    data = load_youth_data()
    return render_template("admin_youth_ministry.html", leaders=data["leaders"], events=data["events"])

@app.route("/add-youth-leader", methods=["POST"])
def add_youth_leader():
    data = load_youth_data()
    name = request.form.get("name")
    role = request.form.get("role")
    photo = request.files.get("photo")
    photo_path = "/static/default_profile.png"
    if photo and photo.filename:
        filename = photo.filename
        save_path = os.path.join(IMAGE_FOLDER, filename)
        photo.save(save_path)
        photo_path = f"/static/uploads/images/{filename}"
    data["leaders"].append({"name": name, "role": role, "photo": photo_path})
    save_youth_data(data)
    return redirect(url_for("admin_youth_ministry"))

@app.route("/delete-youth-leader/<int:index>")
def delete_youth_leader(index):
    data = load_youth_data()
    if 0 <= index < len(data["leaders"]):
        data["leaders"].pop(index)
        save_youth_data(data)
    return redirect(url_for("admin_youth_ministry"))

@app.route("/add-youth-event", methods=["POST"])
def add_youth_event():
    data = load_youth_data()
    data["events"].append({
        "title": request.form.get("title"),
        "date": request.form.get("date"),
        "time": request.form.get("time"),
        "description": request.form.get("description")
    })
    save_youth_data(data)
    return redirect(url_for("admin_youth_ministry"))

@app.route("/delete-youth-event/<int:index>")
def delete_youth_event(index):
    data = load_youth_data()
    if 0 <= index < len(data["events"]):
        data["events"].pop(index)
        save_youth_data(data)
    return redirect(url_for("admin_youth_ministry"))

@app.route("/children-youth")
def children_youth():
    data = load_youth_data()
    return render_template(
        "children_youth.html",
        youth_leaders=data.get("leaders", []),
        youth_events=data.get("events", [])
    )

# ==================== ALL FORM SUBMISSIONS ====================

@app.route("/submit-volunteer", methods=["POST"])
def submit_volunteer():
    try:
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        areas = request.form.getlist("areas")
        message = request.form.get("message", "").strip()

        if not name or not phone:
            flash("Please fill in your name and phone number.", "error")
            return redirect(url_for("join_our_mission"))

        body = f"""
NEW VOLUNTEER APPLICATION
Name: {name}
Phone: {phone}
Email: {email or "Not provided"}
Areas: {", ".join(areas) if areas else "None"}
Message: {message or "None"}
        """
        
        send_email("NEW VOLUNTEER APPLICATION", body)
        flash(f"Thank you {name}! Your volunteer application has been received.", "success")
            
    except Exception as e:
        print(f"VOLUNTEER ERROR: {e}")
        flash("Something went wrong. Please try again.", "error")
    
    return redirect(url_for("join_our_mission"))

@app.route("/submit-minister", methods=["POST"])
def submit_minister():
    try:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        interest = request.form.get("interest", "").strip()
        experience = request.form.get("experience", "").strip()

        if not name or not email:
            flash("Please provide your name and email.", "error")
            return redirect(url_for("join_our_mission"))

        body = f"""
NEW TEACHING MINISTRY APPLICATION
Name: {name}
Email: {email}
Interest: {interest}
Experience: {experience or "None"}
        """
        
        send_email("NEW TEACHING MINISTRY APPLICATION", body)
        flash(f"Thank you {name}! Your interest has been received.", "success")
            
    except Exception as e:
        print(f"MINISTER ERROR: {e}")
        flash("Something went wrong. Please try again.", "error")
    
    return redirect(url_for("join_our_mission"))

@app.route("/submit-testimony", methods=["POST"])
def submit_testimony():
    try:
        name = request.form.get("name", "").strip()
        role = request.form.get("role", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not message:
            flash("Please enter your name and testimony.", "error")
            return redirect(url_for("join_our_mission") + "#testimoniesContainer")

        save_testimony({"name": name, "role": role, "message": message})
        
        body = f"""
NEW TESTIMONY
From: {name} ({role or "Member"})
Message: "{message}"
        """
        
        send_email("NEW TESTIMONY", body)
        flash("Your testimony has been shared!", "success")
        
    except Exception as e:
        print(f"TESTIMONY ERROR: {e}")
        flash("Something went wrong. Please try again.", "error")
    
    return redirect(url_for("join_our_mission") + "#testimoniesContainer")

@app.route("/submit-partnership", methods=["POST"])
def submit_partnership():
    print("=" * 60)
    print("🔍 PARTNERSHIP FORM SUBMITTED")
    
    try:
        org_name = request.form.get("org_name", "").strip()
        contact_person = request.form.get("contact_person", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        vision = request.form.get("vision", "").strip()
        interests = request.form.getlist("interests")

        if not org_name or not contact_person or not email:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("join_our_mission"))

        print(f"✅ Validation passed")

        # Save to JSON
        partnership_data = {
            "org_name": org_name,
            "contact_person": contact_person,
            "email": email,
            "phone": phone,
            "interests": interests,
            "vision": vision,
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_partnership(partnership_data)

        # Log email (no actual sending)
        interests_text = ", ".join(interests) if interests else "None"
        body = f"""
NEW PARTNERSHIP REQUEST!
Organization: {org_name}
Contact: {contact_person}
Email: {email}
Phone: {phone or "N/A"}
Interests: {interests_text}
Vision: {vision or "N/A"}
        """
        
        send_email("NEW PARTNERSHIP REQUEST", body)
        flash("Thank you! Your partnership request has been received!", "success")
        print("✅ Partnership completed")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        flash("Something went wrong. Please try again.", "error")

    return redirect(url_for("join_our_mission"))

# ... (rest of your routes - stream, admin, fellowship, etc. - keep them as they are)

@app.route("/live-stream")
def live_stream():
    try:
        with open('stream_config.json', 'r') as f:
            stream_data = json.load(f)
    except:
        stream_data = {
            'is_live': False,
            'youtube_video_id': '',
            'title': 'Sunday Service Live',
            'description': 'Join us for worship',
            'schedule': 'Every Sunday at 10:00 AM EAT'
        }
    return render_template("live_stream.html", stream=stream_data)

@app.route("/admin/stream-control", methods=["GET", "POST"])
def stream_control():
    if not session.get('admin_logged_in'):
        flash("Please login", "error")
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        data = {
            'is_live': request.form.get('is_live') == 'on',
            'youtube_video_id': request.form.get('youtube_id'),
            'title': request.form.get('title'),
            'description': request.form.get('description', ''),
            'schedule': request.form.get('schedule', 'Every Sunday at 10 AM')
        }
        with open('stream_config.json', 'w') as f:
            json.dump(data, f)
        flash("Stream updated!", "success")
        return redirect(url_for("stream_control"))
    try:
        with open('stream_config.json', 'r') as f:
            stream_data = json.load(f)
    except:
        stream_data = {}
    return render_template("stream_control.html", stream=stream_data)

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "password123":
            session['admin_logged_in'] = True
            flash("Login successful!", "success")
            return redirect(url_for("evangelism"))
        flash("Invalid credentials", "error")
    return render_template("admin_login.html")

@app.route("/admin-logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Logged out.", "success")
    return redirect(url_for("home"))

@app.route("/upload-sermon")
def upload_sermon():
    if not session.get('admin_logged_in'):
        flash("Please login", "error")
        return redirect(url_for("admin_login"))
    return redirect(url_for("evangelism"))

@app.route("/evangelism")
def evangelism():
    if not session.get('admin_logged_in'):
        flash("Please login", "error")
        return redirect(url_for("admin_login"))
    files = get_uploaded_files()
    return render_template("evangelism.html", files=files)

@app.route("/upload-resources", methods=["POST"])
def upload_resources():
    if not session.get('admin_logged_in'):
        flash("Please login", "error")
        return redirect(url_for("admin_login"))
    file_type = request.form.get('file_type')
    if file_type not in ALLOWED_EXTENSIONS:
        flash("Invalid file type", "error")
        return redirect(url_for("evangelism"))
    if "files" not in request.files:
        flash("No files selected", "error")
        return redirect(url_for("evangelism"))
    files = request.files.getlist("files")
    folder_map = {
        'pdf': PDF_FOLDER,
        'documents': DOCUMENT_FOLDER,
        'audio': AUDIO_FOLDER,
        'video': VIDEO_FOLDER,
        'images': IMAGE_FOLDER
    }
    uploaded_count = 0
    skipped_count = 0
    for file in files:
        if file and file.filename:
            filename = file.filename
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in ALLOWED_EXTENSIONS[file_type]:
                filepath = os.path.join(folder_map[file_type], filename)
                try:
                    file.save(filepath)
                    uploaded_count += 1
                except:
                    skipped_count += 1
            else:
                skipped_count += 1
    if uploaded_count > 0:
        flash(f"Uploaded {uploaded_count} files", "success")
    if skipped_count > 0:
        flash(f"Skipped {skipped_count} files", "warning")
    return redirect(url_for("evangelism"))

@app.route("/delete/<file_type>/<filename>")
def delete_file(file_type, filename):
    if not session.get('admin_logged_in'):
        flash("Please login", "error")
        return redirect(url_for("admin_login"))
    folder_map = {
        'pdf': PDF_FOLDER,
        'documents': DOCUMENT_FOLDER,
        'audio': AUDIO_FOLDER,
        'video': VIDEO_FOLDER,
        'images': IMAGE_FOLDER
    }
    if file_type in folder_map:
        file_path = os.path.join(folder_map[file_type], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            flash("File deleted", "success")
        else:
            flash("File not found", "error")
    return redirect(url_for("evangelism"))

@app.route("/uploads/pdf/<filename>")
def serve_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename)

@app.route("/uploads/documents/<filename>")
def serve_document(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        return send_from_directory(DOCUMENT_FOLDER, filename, mimetype='application/pdf')
    elif ext == 'txt':
        return send_from_directory(DOCUMENT_FOLDER, filename, mimetype='text/plain')
    else:
        return send_from_directory(DOCUMENT_FOLDER, filename, as_attachment=True)

@app.route("/fellowship")
def fellowship():
    data = load_fellowship_data()
    return render_template("fellowship.html", fellowship=data)

FELLOWSHIP_DATA_FILE = os.path.join(BASE_DIR, "fellowship_data.json")

def load_fellowship_data():
    if os.path.exists(FELLOWSHIP_DATA_FILE):
        try:
            with open(FELLOWSHIP_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "mens": {"title": "", "motto": "", "meeting": "", "venue": "", "leader": "", "phone": "", "description": "", "themes": []},
        "womens": {"title": "", "motto": "", "meeting": "", "venue": "", "leader": "", "phone": "", "description": "", "themes": []}
    }

def save_fellowship_data(data):
    with open(FELLOWSHIP_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route("/admin-partnerships")
def admin_partnerships():
    if not session.get('admin_logged_in'):
        flash("Please login first", "error")
        return redirect(url_for("admin_login"))
    
    partnerships = []
    if os.path.exists(PARTNERSHIPS_FILE):
        try:
            with open(PARTNERSHIPS_FILE, 'r', encoding='utf-8') as f:
                partnerships = json.load(f)
        except:
            partnerships = []
    
    return render_template("admin_partnerships.html", partnerships=partnerships)

@app.route("/admin-fellowship")
def admin_fellowship():
    if not session.get('admin_logged_in'):
        flash("Please login first", "error")
        return redirect(url_for("admin_login"))
    data = load_fellowship_data()
    return render_template("admin_fellowship.html", fellowship=data)

@app.route("/update-fellowship", methods=["POST"])
def update_fellowship():
    if not session.get('admin_logged_in'):
        return redirect(url_for("admin_login"))
    
    data = load_fellowship_data()
    
    data["mens"] = {
        "title": request.form.get("mens_title", "").strip(),
        "motto": request.form.get("mens_motto", "").strip(),
        "meeting": request.form.get("mens_meeting", "").strip(),
        "venue": request.form.get("mens_venue", "").strip(),
        "leader": request.form.get("mens_leader", "").strip(),
        "phone": request.form.get("mens_phone", "").strip(),
        "description": request.form.get("mens_description", "").strip(),
        "themes": [t.strip() for t in request.form.get("mens_themes", "").split(",") if t.strip()]
    }
    
    data["womens"] = {
        "title": request.form.get("womens_title", "").strip(),
        "motto": request.form.get("womens_motto", "").strip(),
        "meeting": request.form.get("womens_meeting", "").strip(),
        "venue": request.form.get("womens_venue", "").strip(),
        "leader": request.form.get("womens_leader", "").strip(),
        "phone": request.form.get("womens_phone", "").strip(),
        "description": request.form.get("womens_description", "").strip(),
        "themes": [t.strip() for t in request.form.get("womens_themes", "").split(",") if t.strip()]
    }
    
    save_fellowship_data(data)
    flash("Fellowship details saved successfully!", "success")
    return redirect(url_for("admin_fellowship"))

@app.route("/uploads/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

@app.route("/uploads/video/<filename>")
def serve_video(filename):
    return send_from_directory(VIDEO_FOLDER, filename)

@app.route("/uploads/images/<filename>")
def serve_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(413)
def file_too_large(e):
    flash("File too large", "error")
    return redirect(url_for("evangelism"))

if __name__ == "__main__":
    print("🙏 Lord's Harvest Ministry Website is LIVE!")
    app.run(debug=True)