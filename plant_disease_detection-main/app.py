import os
import mysql.connector
from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from flask import send_from_directory
from werkzeug.utils import secure_filename
import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.applications import mobilenet_v3
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'plant_system'
}

# Load the TensorFlow model
model_path = 'model-plant-model2-second-model(1).keras'
try:
    model = load_model(model_path)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

class_names = {0: 'Healthy', 1: 'Powdery', 2: 'Rust', 3: 'Slug', 4: 'Spot'}

def getResult(image_path):
    try:
        image = load_img(image_path, target_size=(224, 224))
        image_array = img_to_array(image)
        image_array = mobilenet_v3.preprocess_input(image_array)
        image_array = np.expand_dims(image_array, axis=0)
        predictions = model.predict(image_array)
        predicted_class = np.argmax(predictions)
        predicted_class_name = class_names[predicted_class]
        probability = predictions[0][predicted_class] * 100
        return predicted_class_name, probability
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None, None

@app.route('/', methods=['GET'])
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/home', methods=['GET'])
def home():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data['username']
        email = data['email']
        password = data['password']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, email, password))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "User registered successfully!"}), 201
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data['username']
        password = data['password']

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT id FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return jsonify({"message": "Login successful!", "redirect": "/home"}), 200
        else:
            return jsonify({"message": "Invalid credentials!"}), 401
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

@app.route('/classifier', methods=['GET', 'POST'])
def classifier():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, 'uploads', secure_filename(file.filename))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

        predicted_class_name, probability = getResult(file_path)
        if predicted_class_name:
            user_id = session['user_id']
            timestamp = datetime.now()
            probability = float(probability)  # Convert NumPy float64 to Python float
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                query = """INSERT INTO classification_history (user_id, image_path, disease_name, probability, timestamp)
                           VALUES (%s, %s, %s, %s, %s)"""
                cursor.execute(query, (user_id, file_path, predicted_class_name, probability, timestamp))
                conn.commit()
                cursor.close()
                conn.close()
            except mysql.connector.Error as err:
                print(f"Database Error: {err}")
                return jsonify({"error": str(err)}), 500
            except Exception as e:
                print(f"Unexpected Error: {e}")
                return jsonify({"error": str(e)}), 500

            return jsonify({
                "class": predicted_class_name,
                "probability": f"{probability:.2f}%"
            })
        else:
            return jsonify({"error": "Prediction failed"}), 500

    return render_template('classifier.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']

    if request.method == 'POST':
        try:
            data = request.json
            new_username = data.get('username')
            new_email = data.get('email')
            new_password = data.get('password')
            confirm_password = data.get('confirm_password')

            # Check if passwords match
            if new_password != confirm_password:
                return jsonify({"error": "Passwords do not match"}), 400

            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Update user details
            query = "UPDATE users SET username = %s, email = %s, password = %s WHERE id = %s"
            cursor.execute(query, (new_username, new_email, new_password, user_id))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({"message": "Profile updated successfully!"}), 200
        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 400

    # Fetch current user details for display
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = "SELECT username, email FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            return render_template('profile.html', username=user[0], email=user[1])
        else:
            return redirect(url_for('index'))
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'uploads'), filename)

@app.route('/history', methods=['GET'])
def history():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = """SELECT image_path, disease_name, probability, timestamp
                   FROM classification_history WHERE user_id = %s ORDER BY timestamp DESC"""
        cursor.execute(query, (user_id,))
        history_records = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('history.html', history=history_records)
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500



@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
