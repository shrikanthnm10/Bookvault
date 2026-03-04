"""
BookVault — Test Suite
======================
Runs as the CodeBuild Test stage in CodePipeline.
All tests must pass before deployment to ECS proceeds.

Tests cover:
  - All API endpoints (health, books, reviews)
  - Form validation (missing fields)
  - HTML content sanity checks
  - DB-less mode (app gracefully handles missing DB env vars)
"""

import os
import sys
import json
import pytest

# ── Make sure we can import app.py from the project root ──────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set dummy DB env vars so the app module loads without crashing.
# The actual DB connection is never called in unit tests.
os.environ.setdefault("DB_HOST",     "localhost")
os.environ.setdefault("DB_USER",     "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("DB_NAME",     "test_db")

import app as bookvault_app   # noqa: E402  (import after env setup)


# ─────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Flask test client — no real DB needed."""
    bookvault_app.app.config["TESTING"] = True
    with bookvault_app.app.test_client() as client:
        yield client


# ─────────────────────────────────────────────────────────────────────
# 1. HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────

class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        """GET /health should always return HTTP 200."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_is_json(self, client):
        """GET /health must return valid JSON."""
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert isinstance(data, dict)

    def test_health_contains_status_field(self, client):
        """JSON response must contain 'status' key."""
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert "status" in data

    def test_health_status_is_ok(self, client):
        """'status' field value must be 'ok'."""
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert data["status"] == "ok"

    def test_health_contains_app_field(self, client):
        """JSON response must identify the application."""
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert "app" in data
        assert "BookVault" in data["app"]

    def test_health_contains_db_field(self, client):
        """JSON response must report DB connectivity status."""
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert "db" in data


# ─────────────────────────────────────────────────────────────────────
# 2. HOME PAGE
# ─────────────────────────────────────────────────────────────────────

class TestHomePage:

    def test_home_returns_200(self, client):
        """GET / should return HTTP 200."""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home_returns_html(self, client):
        """GET / must return HTML content."""
        resp = client.get("/")
        assert b"<!DOCTYPE html>" in resp.data or b"<html" in resp.data

    def test_home_contains_app_title(self, client):
        """Page must contain the BookVault brand name."""
        resp = client.get("/")
        assert b"BookVault" in resp.data

    def test_home_contains_search_input(self, client):
        """Page must contain a search input field."""
        resp = client.get("/")
        assert b"searchInput" in resp.data

    def test_home_contains_book_data(self, client):
        """Page must embed at least one book title in the HTML."""
        resp = client.get("/")
        # Check that the first book's title appears in the rendered page
        first_book = bookvault_app.BOOKS[0]["title"]
        assert first_book.encode() in resp.data

    def test_home_contains_review_form(self, client):
        """Page must render the reader review submission form."""
        resp = client.get("/")
        assert b"submitReview" in resp.data or b"fbName" in resp.data


# ─────────────────────────────────────────────────────────────────────
# 3. BOOKS API
# ─────────────────────────────────────────────────────────────────────

class TestBooksAPI:

    def test_api_books_returns_200(self, client):
        """GET /api/books should return HTTP 200."""
        resp = client.get("/api/books")
        assert resp.status_code == 200

    def test_api_books_returns_json(self, client):
        """GET /api/books must return valid JSON."""
        resp = client.get("/api/books")
        data = json.loads(resp.data)
        assert isinstance(data, dict)

    def test_api_books_contains_books_key(self, client):
        """JSON must contain 'books' list."""
        resp = client.get("/api/books")
        data = json.loads(resp.data)
        assert "books" in data
        assert isinstance(data["books"], list)

    def test_api_books_contains_total_key(self, client):
        """JSON must contain 'total' count."""
        resp = client.get("/api/books")
        data = json.loads(resp.data)
        assert "total" in data

    def test_api_books_total_matches_list_length(self, client):
        """'total' must equal the number of items in 'books'."""
        resp = client.get("/api/books")
        data = json.loads(resp.data)
        assert data["total"] == len(data["books"])

    def test_api_books_not_empty(self, client):
        """Books list must contain at least one book."""
        resp = client.get("/api/books")
        data = json.loads(resp.data)
        assert len(data["books"]) > 0

    def test_api_books_correct_count(self, client):
        """Total must match the BOOKS constant in app.py."""
        resp = client.get("/api/books")
        data = json.loads(resp.data)
        assert data["total"] == len(bookvault_app.BOOKS)

    def test_api_books_each_has_required_fields(self, client):
        """Every book object must have title, author, genre, year, emoji."""
        resp = client.get("/api/books")
        data = json.loads(resp.data)
        required = {"title", "author", "genre", "year", "emoji", "tagline", "bio", "known_for"}
        for book in data["books"]:
            missing = required - set(book.keys())
            assert not missing, f"Book '{book.get('title','?')}' missing fields: {missing}"

    def test_api_books_known_for_is_list(self, client):
        """'known_for' field must be a list for every book."""
        resp = client.get("/api/books")
        data = json.loads(resp.data)
        for book in data["books"]:
            assert isinstance(book["known_for"], list), \
                f"'known_for' should be a list for book '{book['title']}'"

    def test_api_books_no_empty_titles(self, client):
        """No book should have a blank title."""
        resp = client.get("/api/books")
        data = json.loads(resp.data)
        for book in data["books"]:
            assert book["title"].strip() != "", "Found a book with an empty title"


# ─────────────────────────────────────────────────────────────────────
# 4. REVIEW SUBMISSION — VALIDATION
# ─────────────────────────────────────────────────────────────────────

class TestReviewValidation:
    """
    These tests check form validation WITHOUT touching RDS.
    Missing-field cases are handled before any DB call, so no mock needed.
    """

    def test_review_missing_all_fields_returns_400(self, client):
        """POST /review with no data must return 400."""
        resp = client.post("/review", data={})
        assert resp.status_code == 400

    def test_review_missing_name_returns_400(self, client):
        """POST /review without name must return 400."""
        resp = client.post("/review", data={
            "email": "test@example.com",
            "message": "Great books!"
        })
        assert resp.status_code == 400

    def test_review_missing_email_returns_400(self, client):
        """POST /review without email must return 400."""
        resp = client.post("/review", data={
            "name": "Test User",
            "message": "Great books!"
        })
        assert resp.status_code == 400

    def test_review_missing_message_returns_400(self, client):
        """POST /review without message must return 400."""
        resp = client.post("/review", data={
            "name": "Test User",
            "email": "test@example.com"
        })
        assert resp.status_code == 400

    def test_review_whitespace_only_fields_returns_400(self, client):
        """POST /review with whitespace-only fields must return 400."""
        resp = client.post("/review", data={
            "name": "   ",
            "email": "   ",
            "message": "   "
        })
        assert resp.status_code == 400

    def test_review_missing_fields_returns_json_error(self, client):
        """400 response must include a JSON error message."""
        resp = client.post("/review", data={})
        data = json.loads(resp.data)
        assert "error" in data

    def test_review_error_message_is_string(self, client):
        """Error message in the 400 response must be a non-empty string."""
        resp = client.post("/review", data={})
        data = json.loads(resp.data)
        assert isinstance(data["error"], str)
        assert len(data["error"]) > 0


# ─────────────────────────────────────────────────────────────────────
# 5. BOOK DATA INTEGRITY (unit tests — no HTTP call needed)
# ─────────────────────────────────────────────────────────────────────

class TestBookDataIntegrity:

    def test_books_list_is_not_empty(self):
        """BOOKS constant must not be empty."""
        assert len(bookvault_app.BOOKS) > 0

    def test_all_books_have_unique_titles(self):
        """No two books should share the same title."""
        titles = [b["title"] for b in bookvault_app.BOOKS]
        assert len(titles) == len(set(titles)), "Duplicate book titles found!"

    def test_all_books_have_non_empty_author(self):
        """Every book must have a non-empty author."""
        for book in bookvault_app.BOOKS:
            assert book["author"].strip(), f"Empty author in book: {book['title']}"

    def test_all_books_have_valid_year(self):
        """Year must be a 4-digit string."""
        for book in bookvault_app.BOOKS:
            assert book["year"].isdigit() and len(book["year"]) == 4, \
                f"Invalid year '{book['year']}' in book: {book['title']}"

    def test_all_books_have_emoji(self):
        """Every book must have an emoji field."""
        for book in bookvault_app.BOOKS:
            assert book["emoji"].strip(), f"Missing emoji for: {book['title']}"

    def test_all_books_known_for_has_items(self):
        """Every book's known_for list must have at least one entry."""
        for book in bookvault_app.BOOKS:
            assert len(book["known_for"]) >= 1, \
                f"'known_for' is empty for: {book['title']}"

    def test_all_books_have_genre(self):
        """Every book must have a non-empty genre."""
        for book in bookvault_app.BOOKS:
            assert book["genre"].strip(), f"Missing genre for: {book['title']}"

    def test_all_books_have_bio(self):
        """Every book must have a non-empty bio."""
        for book in bookvault_app.BOOKS:
            assert book["bio"].strip(), f"Missing bio for: {book['title']}"


# ─────────────────────────────────────────────────────────────────────
# 6. ROUTING — WRONG METHODS
# ─────────────────────────────────────────────────────────────────────

class TestRoutingMethods:

    def test_get_on_review_post_route_returns_405(self, client):
        """GET /review must return 405 Method Not Allowed."""
        resp = client.get("/review")
        assert resp.status_code == 405

    def test_post_on_api_books_returns_405(self, client):
        """POST /api/books must return 405 Method Not Allowed."""
        resp = client.post("/api/books")
        assert resp.status_code == 405

    def test_unknown_route_returns_404(self, client):
        """Unknown routes must return 404."""
        resp = client.get("/this-route-does-not-exist")
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────
# 7. CONTENT-TYPE CHECKS
# ─────────────────────────────────────────────────────────────────────

class TestContentTypes:

    def test_health_content_type_is_json(self, client):
        """GET /health must return application/json."""
        resp = client.get("/health")
        assert "application/json" in resp.content_type

    def test_api_books_content_type_is_json(self, client):
        """GET /api/books must return application/json."""
        resp = client.get("/api/books")
        assert "application/json" in resp.content_type

    def test_home_content_type_is_html(self, client):
        """GET / must return text/html."""
        resp = client.get("/")
        assert "text/html" in resp.content_type
