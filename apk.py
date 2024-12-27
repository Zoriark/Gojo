import streamlit as st
import sqlite3
import hashlib
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database setup (SQLite)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)''')
conn.commit()

# Hashing password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Verify password function
def verify_password(stored_hash, password):
    return stored_hash == hash_password(password)

# Register user function
def register_user(username, password):
    password_hash = hash_password(password)
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        st.success("User registered successfully!")
    except sqlite3.IntegrityError:
        st.error("Username already exists!")

# Login user function
def login_user(username, password):
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if result:
        stored_hash = result[0]
        if verify_password(stored_hash, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success("Login successful!")
            return True
        else:
            st.error("Incorrect password!")
            return False
    else:
        st.error("Username not found!")
        return False

# Weather functions
def get_current_weather(city, api_key):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            'city_name': data['name'],
            'country': data['sys']['country'],
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'weather_description': data['weather'][0]['description'],
            'wind_speed': data['wind']['speed'],
            'icon_code': data['weather'][0]['icon']
        }
    else:
        return None

def get_5day_forecast(city, api_key):
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        forecast = {}
        for entry in data['list']:
            timestamp = entry['dt']
            date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
            temp = entry['main']['temp']
            weather_description = entry['weather'][0]['description']
            time = datetime.utcfromtimestamp(timestamp).strftime('%H:%M')
            icon_code = entry['weather'][0]['icon']
            if date not in forecast:
                forecast[date] = []
            forecast[date].append({
                'time': time,
                'temp': temp,
                'weather_description': weather_description,
                'icon_code': icon_code
            })
        return forecast
    else:
        return None

# Streamlit app
def app():
    # Authentication UI
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        menu = ["Login", "Register"]
        choice = st.sidebar.selectbox("Choose Option", menu)

        if choice == "Register":
            st.subheader("Create a New Account")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            if st.button("Register"):
                if password == confirm_password:
                    register_user(username, password)
                else:
                    st.error("Passwords do not match!")

        elif choice == "Login":
            st.subheader("Login to Your Account")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                if login_user(username, password):
                    st.session_state['username'] = username
                    st.rerun()

    # Weather UI (After Login)
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        st.markdown(f"**Hello, {st.session_state['username']}!**")
        st.markdown("""<div style="font-size:30px; color:blue; font-weight:bold; text-align:center;">Weather Forecast App</div>""", unsafe_allow_html=True)

        city = st.text_input("Enter city name:", "")
        api_key = "e21130092264b383b3fc9b0b7975cdcc"  # Get API key from environment variables

        if not api_key:
            st.warning("API Key is missing! Please set it in your environment.")

        if city and api_key:
            current_weather = get_current_weather(city, api_key)
            if current_weather:
                st.subheader(f"Current Weather for {current_weather['city_name']}, {current_weather['country']}")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Temperature:** {current_weather['temperature']}°C")
                    st.markdown(f"**Humidity:** {current_weather['humidity']}%")
                    st.markdown(f"**Wind Speed:** {current_weather['wind_speed']} m/s")

                with col2:
                    st.markdown(f"**Weather:** {current_weather['weather_description']}")
                    icon_url = f"http://openweathermap.org/img/wn/{current_weather['icon_code']}@2x.png"
                    st.image(icon_url, width=100)
            else:
                st.error("Error: Unable to get current weather data. Please check the city name or API key.")

            # Display 5-day forecast
            st.subheader("5-Day Weather Forecast:")
            forecast = get_5day_forecast(city, api_key)
            if forecast:
                for day, details in forecast.items():
                    st.markdown(f'<div style="background-color: #00FFFF; padding: 10px; border-radius: 25px; font-weight: bold; font-size: 20px; text-align: center; margin-bottom: 10px;">{day}</div>', unsafe_allow_html=True)
                    for detail in details:
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col1:
                            st.write(f"{detail['time']}")
                        with col2:
                            st.write(f"**Temp:** {detail['temp']}°C")
                            st.write(f"**Weather:** {detail['weather_description']}")
                        with col3:
                            icon_url = f"http://openweathermap.org/img/wn/{detail['icon_code']}@2x.png"
                            st.image(icon_url, width=50)
            else:
                st.error("Error: Unable to get 5-day forecast data. Please check the city name or API key.")

if __name__ == "__main__":
    app()
