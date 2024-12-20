from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from sqlalchemy import create_engine, URL, text
from sqlalchemy.orm import sessionmaker
from html_tamplates import html_base
import requests

# Skapa en SQLAlchemy Engine
url = URL.create(
    drivername="postgresql+psycopg2",
    port="5544",
    username="postgres",
    password="abc123",
    host="localhost",
    database="dm23"
)
engine = create_engine(url)

# Skapa en Flask-app
app = Flask(__name__)

# Skapa en Session Factory för att hantera databasanslutningar
Session = sessionmaker(bind=engine)

# Route för att skapa en ny användare
@app.post('/users')
def create_user():
    # Hantera både JSON- och formulärdata
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
    else:
        name = request.form.get('name')
        email = request.form.get('email')

    # Validering av input
    if not name or not email:
        return jsonify({"error": "Invalid input. Please fill in all fields."}), 400

    # Använd en session för databasoperationer
    with Session() as session:
        # Kontrollera om e-post redan används
        result = session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
        if result:
            return jsonify({"error": "Email already in use."}), 409

        # Skapa en ny användare
        session.execute(
            text("INSERT INTO users (name, email) VALUES (:name, :email)"),
            {"name": name, "email": email}
        )
        session.commit()

    # Returnera vid lyckad registrering
    return jsonify({"message": f"User '{name}' created successfully"}), 201

# Route för att hämta alla användare
@app.get('/users')
def get_users():
    with Session() as session:
        # Hämta alla användare från databasen
        result = session.execute(text("SELECT * FROM users")).fetchall()

        # Konvertera till en lista med dictionaries
        users_list = [{"id": row.id, "name": row.name, "email": row.email} for row in result]

    return jsonify(users_list), 200


# Route för att visa registreringsformuläret och hantera inmatningar
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""
    if request.method == 'POST':
        # Hämta inmatade data från formuläret
        name = request.form.get('name')
        email = request.form.get('email')

        # Skicka en POST-request till /users
        response = requests.post(
            url_for('create_user', _external=True),
            json={"name": name, "email": email}
        )

        # Kontrollera svaret
        if response.status_code == 201:  # Lyckad registrering
            return redirect(url_for('success'))
        elif response.status_code == 400:  # Ogiltig input
            message = "Invalid input. Please fill in all fields."
        elif response.status_code == 409:  # E-post redan används
            message = "Email already in use. Try a different one."

    # Visa formuläret igen med meddelandet om det fanns ett fel
    return render_template_string(html_base("Registration", """
    <h1>User Registration</h1>
    <form action="{{ url_for('register') }}" method="post">
        <label for="name">Name:</label><br>
        <input type="text" id="name" name="name" required><br><br>
        <label for="email">Email:</label><br>
        <input type="email" id="email" name="email" required><br><br>
        <button type="submit">Register</button>
    </form>
    <p>{{ message }}</p>"""), message=message)

# Route för lyckad registrering
@app.route('/success')
def success():
    return html_base("Success", """
        <h1>Registration Successful!</h1>
        <a href="/register">Register another user</a>
        """)

# if __name__ == "__main__":
#    app.run(debug=True)

