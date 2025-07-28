import os
import shutil
import re
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox, Text
from dotenv import load_dotenv
from datetime import datetime, timedelta
import subprocess

load_dotenv()

HTML_FILE = os.getenv("HTML_FILE")
HIGHLIGHT_DIR = os.getenv("IMAGE_HIGHLIGHT_DIR")
GALLERY_DIR = os.getenv("IMAGE_GALLERY_DIR")
ARCHIVE_DIR = os.getenv("ARCHIVE_HIGHLIGHT_DIR")

def classify_result(score):
    try:
        home, away = map(int, score.strip().split("-"))
        if home > away:
            return "win"
        elif home < away:
            return "loss"
        else:
            return "draw"
    except:
        return ""

def get_next_sunday():
    today = datetime.today().date()
    days_ahead = 6 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + timedelta(days=days_ahead)

def update_upcoming_match(html):
    match = re.search(r'<span class="match-date">([A-Za-z]+ \d{1,2}, \d{4})</span>', html)
    if match:
        old_date_str = match.group(1)
        try:
            old_date = datetime.strptime(old_date_str, "%B %d, %Y").date()
            if old_date < datetime.today().date():
                next_sunday = get_next_sunday()
                new_date_str = next_sunday.strftime("%B %d, %Y")
                html = html.replace(old_date_str, new_date_str)
        except Exception as e:
            print(f"Error parsing upcoming match date: {e}")
    return html


def update_html(match_title, match_date, score, description, image_filename):
    with open(HTML_FILE, "r", encoding="utf-8") as file:
        html = file.read()

    # Move old highlight image
    old_img_match = re.search(r"highlights/([^']+\.(jpg|png|jpeg))", html)
    if old_img_match:
        old_img = old_img_match.group(1)
        old_img_path = os.path.join(HIGHLIGHT_DIR, old_img)
        if os.path.exists(old_img_path):
            shutil.move(old_img_path, os.path.join(ARCHIVE_DIR, old_img))

    # Update Match Highlight section
    new_highlight = f'''
        <section class="section">
            <h2 class="section-title">Match Highlight</h2>
            <div class="match-highlight">
                <div class="match-highlight-img" style="background-image: url('images/highlights/{image_filename}');"></div>
                <div class="match-highlight-info">
                    <h3>{match_title}</h3>
                    <p class="match-details">{match_date}</p>
                    <div class="match-highlight-score">{score}</div>
                    <p>{description}</p>
                </div>
            </div>
        </section>
    '''
    html = re.sub(r'<section class="section">\s*<h2 class="section-title">Match Highlight</h2>.*?</section>', new_highlight, html, flags=re.DOTALL)

    # Add match-card at top
    result_class = classify_result(score)
    match_card = f"""
            <div class="match-card">
                <div>
                    <div class="match-teams">{match_title}</div>
                    <div class="match-details">{match_date}</div>
                </div>
                <div class="match-result {result_class}">{score}</div>
            </div>
    """
    html = re.sub(r'(<section class="section" id="matches">.*?<h2 class="section-title">Matches & Results</h2>)', r'\1' + match_card, html, flags=re.DOTALL)

    # Add gallery image
    gallery_slide = f'<div class="gallery-slide" style="background-image: url(\'images/gallery/{image_filename}\');"></div>'
    html = re.sub(r'(</div>\s*</section>\s*<!-- Sponsors Section -->)', gallery_slide + r'\1', html, flags=re.DOTALL)

    # Update upcoming match date
    html = update_upcoming_match(html)

    with open(HTML_FILE, "w", encoding="utf-8") as file:
        file.write(html)

def git_push():
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Automated match update"], check=True)
    subprocess.run(["git", "push"], check=True)

def browse_image():
    filepath = filedialog.askopenfilename(title="Select Match Image", filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if filepath:
        image_path_entry.delete(0, "end")
        image_path_entry.insert(0, filepath)

def submit():
    title = title_entry.get()
    date = date_entry.get()
    score = score_entry.get()
    desc = desc_entry.get("1.0", "end").strip()
    image_path = image_path_entry.get()

    if not all([title, date, score, desc, image_path]):
        messagebox.showerror("Missing Info", "Please fill in all fields and select an image.")
        return

    filename = os.path.basename(image_path)
    shutil.copy(image_path, os.path.join(HIGHLIGHT_DIR, filename))
    shutil.copy(image_path, os.path.join(GALLERY_DIR, filename))

    try:
        update_html(title, date, score, desc, filename)
        git_push()
        messagebox.showinfo("Success", "Website updated and pushed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong: {e}")

# GUI Setup
app = Tk()
app.title("⚽ Umarabad FC Updater")
app.geometry("500x500")

Label(app, text="Match Title").pack()
title_entry = Entry(app, width=60)
title_entry.pack()

Label(app, text="Date & Ground").pack()
date_entry = Entry(app, width=60)
date_entry.pack()

Label(app, text="Scoreline (e.g. 3-1)").pack()
score_entry = Entry(app, width=60)
score_entry.pack()

Label(app, text="Highlight Description").pack()
desc_entry = Text(app, height=5, width=60)
desc_entry.pack()

Label(app, text="Image File").pack()
image_path_entry = Entry(app, width=45)
image_path_entry.pack()
Button(app, text="Browse", command=browse_image).pack()

Button(app, text="Submit & Push", command=submit).pack(pady=20)
app.mainloop()
