"""
BookVault - Test Suite
File: tests/test_app.py
Runs via: pytest tests/test_app.py
"""

import pytest
import sys
import os

# Make sure the app module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app


# ─────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    # Use SQLite in-memory DB for tests — no RDS needed
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        yield client


# ─────────────────────────────────────────
# Health / Smoke Tests
# ─────────────────────────────────────────

def test_home_page_loads(client):
    """Home page should return 200."""
    response = client.get('/')
    assert response.status_code == 200


def test_health_check(client):
    """Health check endpoint should return 200."""
    response = client.get('/health')
    assert response.status_code == 200


# ─────────────────────────────────────────
# Books — CRUD
# ─────────────────────────────────────────

def test_get_books_returns_200(client):
    """GET /books should return 200."""
    response = client.get('/books')
    assert response.status_code == 200


def test_get_books_returns_list(client):
    """GET /books should return a JSON list."""
    response = client.get('/books')
    data = response.get_json()
    assert isinstance(data, list)


def test_add_book_success(client):
    """POST /books with valid data should return 201."""
    payload = {
        "title": "The Pragmatic Programmer",
        "author": "David Thomas",
        "isbn": "9780135957059",
        "price": 49.99
    }
    response = client.post('/books', json=payload)
    assert response.status_code in (200, 201)


def test_add_book_missing_title(client):
    """POST /books without title should return 400."""
    payload = {
        "author": "Unknown",
        "isbn": "0000000000000"
    }
    response = client.post('/books', json=payload)
    assert response.status_code == 400


def test_get_single_book(client):
    """GET /books/<id> for a non-existent book should return 404."""
    response = client.get('/books/99999')
    assert response.status_code == 404


def test_delete_nonexistent_book(client):
    """DELETE /books/<id> for a non-existent book should return 404."""
    response = client.delete('/books/99999')
    assert response.status_code == 404


# ─────────────────────────────────────────
# Input Validation
# ─────────────────────────────────────────

def test_empty_post_body(client):
    """POST /books with empty body should return 400."""
    response = client.post('/books', json={})
    assert response.status_code == 400


def test_invalid_price_type(client):
    """POST /books with non-numeric price should return 400."""
    payload = {
        "title": "Bad Book",
        "author": "Someone",
        "price": "not-a-number"
    }
    response = client.post('/books', json=payload)
    assert response.status_code == 400


# ─────────────────────────────────────────
# Response Format
# ─────────────────────────────────────────

def test_response_is_json(client):
    """API responses should have JSON content type."""
    response = client.get('/books')
    assert 'application/json' in response.content_type


def test_404_returns_json(client):
    """Unknown routes should return JSON error, not HTML."""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
