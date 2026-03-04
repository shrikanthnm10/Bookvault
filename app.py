import os
import pymysql
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────────────────────────────
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "bookdb"),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    )


# ─────────────────────────────────────────────────────────────────
# INIT DATABASE
# ─────────────────────────────────────────────────────────────────
def init_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(150) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        conn.close()
        print("✅ Database table ready.")
    except Exception as e:
        print(f"⚠️ DB init warning: {e}")


# ─────────────────────────────────────────────────────────────────
# BOOK DATA (UI)
# ─────────────────────────────────────────────────────────────────
BOOKS = [
    {"title": "1984", "author": "George Orwell", "genre": "Dystopian"},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "genre": "Fantasy"},
    {"title": "Sapiens", "author": "Yuval Noah Harari", "genre": "Non-Fiction"},
]

# ─────────────────────────────────────────────────────────────────
# HTML TEMPLATE
# (kept simple for readability — your UI still works)
# ─────────────────────────────────────────────────────────────────
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<title>BookVault</title>
<style>
body{font-family:Arial;background:#111;color:white;text-align:center;padding:40px}
.card{background:#222;padding:20px;margin:10px;border-radius:8px}
</style>
</head>
<body>

<h1>📚 BookVault</h1>
<p>Classic Book Directory</p>

<div>
{% for book in books %}
<div class="card">
<h3>{{book.title}}</h3>
<p>{{book.author}}</p>
<p>{{book.genre}}</p>
</div>
{% endfor %}
</div>

</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, books=BOOKS)


# ─────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    db_status = "ok"
    try:
        conn = get_db_connection()
        conn.close()
    except Exception as e:
        db_status = str(e)

    return jsonify({
        "status": "ok",
        "db": db_status,
        "service": "bookvault"
    })


# ─────────────────────────────────────────────────────────────────
# FRONTEND API
# ─────────────────────────────────────────────────────────────────
@app.route("/api/books")
def api_books():
    return jsonify({"books": BOOKS})


# ─────────────────────────────────────────────────────────────────
# REVIEW API (RDS)
# ─────────────────────────────────────────────────────────────────
@app.route("/review", methods=["POST"])
def submit_review():

    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    if not name or not email or not message:
        return jsonify({"error": "All fields required"}), 400

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO reviews (name,email,message) VALUES (%s,%s,%s)",
                (name, email, message)
            )

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reviews")
def reviews():

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM reviews ORDER BY created_at DESC LIMIT 50")
            data = cursor.fetchall()

        conn.close()

        return jsonify({"reviews": data})

    except Exception as e:
        return jsonify({"error": str(e), "reviews": []})


# ─────────────────────────────────────────────────────────────────
# TEST API (FOR PYTEST / CI PIPELINE)
# ─────────────────────────────────────────────────────────────────

TEST_BOOKS = []


@app.route("/books", methods=["GET"])
def get_books():
    return jsonify(TEST_BOOKS), 200


@app.route("/books/<int:book_id>", methods=["GET"])
def get_single_book(book_id):

    if book_id >= len(TEST_BOOKS):
        return jsonify({"error": "Book not found"}), 404

    return jsonify(TEST_BOOKS[book_id]), 200


@app.route("/books", methods=["POST"])
def add_book():

    data = request.get_json()

    if not data:
        return jsonify({"error": "Empty body"}), 400

    if "title" not in data:
        return jsonify({"error": "Title required"}), 400

    price = data.get("price")

    if price is not None and not isinstance(price, (int, float)):
        return jsonify({"error": "Invalid price"}), 400

    book = {
        "id": len(TEST_BOOKS),
        "title": data["title"],
        "price": price
    }

    TEST_BOOKS.append(book)

    return jsonify(book), 201


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):

    if book_id >= len(TEST_BOOKS):
        return jsonify({"error": "Book not found"}), 404

    TEST_BOOKS.pop(book_id)

    return jsonify({"message": "deleted"}), 200


# ─────────────────────────────────────────────────────────────────
# RUN APP
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
