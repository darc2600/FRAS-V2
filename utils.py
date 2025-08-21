def load_images_from_folder(folder):
    images = []
    for filename in os.listdir(folder):
        img_path = os.path.join(folder, filename)
        if os.path.isfile(img_path):
            img = cv2.imread(img_path)
            if img is not None:
                images.append(img)
    return images

def save_attendance_record(student_id, timestamp):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance
                      (id INTEGER PRIMARY KEY, student_id TEXT, timestamp TEXT)''')
    cursor.execute('INSERT INTO attendance (student_id, timestamp) VALUES (?, ?)', (student_id, timestamp))
    conn.commit()
    conn.close()

def get_attendance_records():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM attendance')
    records = cursor.fetchall()
    conn.close()
    return records

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (200, 200))
    return resized