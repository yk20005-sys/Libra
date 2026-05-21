import json
import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'musfile-mega-social-key'

# Файлы БД
USERS_FILE = 'users.json'
TRACKS_FILE = 'tracks.json'
MESSAGES_FILE = 'messages.json'

def init_files():
    for file in [USERS_FILE, TRACKS_FILE, MESSAGES_FILE]:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump([], f)

def read_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- КЛАСС ПОЛЬЗОВАТЕЛЯ ---
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']

        self.favorites = user_data.get('favorites', [])
        self.friends = user_data.get('friends', [])


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    users = read_json(USERS_FILE)
    user_data = next((u for u in users if str(u['id']) == str(user_id)), None)
    if user_data:
        return User(user_data)
    return None

# ---  ГЛАВНАЯ И ТРЕКИ ---

@app.route('/')
def index():
    selected_mood = request.args.get('mood')
    all_tracks = read_json(TRACKS_FILE)
    if selected_mood:
        tracks = [t for t in all_tracks if t['mood'] == selected_mood]
    else:
        tracks = all_tracks
    moods = ['Chill', 'Energetic', 'Sad', 'Focus', 'Party', 'Dark']
    return render_template('index.html', tracks=tracks, selected_mood=selected_mood, available_moods=moods)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_track():
    if request.method == 'POST':
        tracks = read_json(TRACKS_FILE)
        new_track = {
            "id": len(tracks) + 1,
            "title": request.form['title'],
            "artist": request.form['artist'],
            "mood": request.form['mood'],
            "link": request.form['link'],
            "author": current_user.username
        }
        tracks.append(new_track)
        write_json(TRACKS_FILE, tracks)
        return redirect(url_for('index'))
    moods = ['Chill', 'Energetic', 'Sad', 'Focus', 'Party', 'Dark']
    return render_template('add_track.html', available_moods=moods)

# ---ИЗБРАННОЕ, ЧАТ ---

@app.route('/favorites')
@login_required
def favorites():
    all_tracks = read_json(TRACKS_FILE)
    fav_tracks = [t for t in all_tracks if t['id'] in current_user.favorites]
    return render_template('index.html', tracks=fav_tracks, title="Избранное")

@app.route('/toggle_fav/<int:track_id>')
@login_required
def toggle_fav(track_id):
    users = read_json(USERS_FILE)
    for u in users:
        if u['username'] == current_user.username:
            if 'favorites' not in u: u['favorites'] = []
            if track_id in u['favorites']:
                u['favorites'].remove(track_id)
            else:
                u['favorites'].append(track_id)
    write_json(USERS_FILE, users)
    return redirect(request.referrer or url_for('index'))

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        messages = read_json(MESSAGES_FILE)
        new_msg = {
            "user": current_user.username,
            "text": request.form['message'],
            "time": datetime.now().strftime("%H:%M")
        }
        messages.append(new_msg)
        write_json(MESSAGES_FILE, messages[-50:])
        return redirect(url_for('chat'))
    messages = read_json(MESSAGES_FILE)
    return render_template('chat.html', messages=messages)

# --- АККАУНТ ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = read_json(USERS_FILE)
        username = request.form['username']
        if any(u['username'] == username for u in users):
            flash('Логин занят!', 'danger')
            return redirect(url_for('register'))
        new_user = {
            "id": len(users) + 1,
            "username": username,
            "password": generate_password_hash(request.form['password'], method='pbkdf2:sha256'),
            "favorites": [],
            "friends": []
        }
        users.append(new_user)
        write_json(USERS_FILE, users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = read_json(USERS_FILE)
        user_data = next((u for u in users if u['username'] == request.form['username']), None)
        if user_data and check_password_hash(user_data['password'], request.form['password']):
            login_user(User(user_data))
            return redirect(url_for('index'))
        flash('Ошибка входа', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_files()
    app.run(debug=True)


