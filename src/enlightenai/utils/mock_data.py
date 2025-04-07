"""
EnlightenAI - Mock Data

This module provides mock data for testing EnlightenAI.
"""

from typing import Dict, Any


def create_mock_data() -> Dict[str, Any]:
    """Create mock data for testing EnlightenAI.
    
    Returns:
        dict: Dictionary containing mock data
    """
    # Mock files
    files = {
        "main.py": """
import config
from models import User
from database import Database
from api import create_app

def main():
    db = Database(config.DB_URL)
    app = create_app(db)
    app.run(host=config.HOST, port=config.PORT)

if __name__ == "__main__":
    main()
""",
        "config.py": """
# Database configuration
DB_URL = "sqlite:///app.db"

# Server configuration
HOST = "0.0.0.0"
PORT = 8000

# API configuration
DEBUG = True
API_VERSION = "v1"
""",
        "models/user.py": """
class User:
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }
""",
        "models/post.py": """
class Post:
    def __init__(self, id, user_id, title, content):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.content = content
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content
        }
""",
        "database.py": """
import sqlite3

class Database:
    def __init__(self, db_url):
        self.db_url = db_url
        self.conn = None
    
    def connect(self):
        self.conn = sqlite3.connect(self.db_url)
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def execute(self, query, params=None):
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor
""",
        "api/__init__.py": """
from flask import Flask

def create_app(db):
    app = Flask(__name__)
    
    from .routes import register_routes
    register_routes(app, db)
    
    return app
""",
        "api/routes.py": """
from flask import jsonify, request
from models import User, Post

def register_routes(app, db):
    @app.route("/api/users", methods=["GET"])
    def get_users():
        cursor = db.execute("SELECT id, username, email FROM users")
        users = [User(row[0], row[1], row[2]).to_dict() for row in cursor.fetchall()]
        return jsonify(users)
    
    @app.route("/api/users/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        cursor = db.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            user = User(row[0], row[1], row[2]).to_dict()
            return jsonify(user)
        return jsonify({"error": "User not found"}), 404
    
    @app.route("/api/posts", methods=["GET"])
    def get_posts():
        cursor = db.execute("SELECT id, user_id, title, content FROM posts")
        posts = [Post(row[0], row[1], row[2], row[3]).to_dict() for row in cursor.fetchall()]
        return jsonify(posts)
    
    @app.route("/api/posts/<int:post_id>", methods=["GET"])
    def get_post(post_id):
        cursor = db.execute("SELECT id, user_id, title, content FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        if row:
            post = Post(row[0], row[1], row[2], row[3]).to_dict()
            return jsonify(post)
        return jsonify({"error": "Post not found"}), 404
"""
    }
    
    # Mock abstractions
    abstractions = [
        {
            "name": "Application Entry Point",
            "description": "The main entry point for the application that initializes and runs the server.",
            "files": ["main.py"]
        },
        {
            "name": "Configuration",
            "description": "Configuration settings for the application, including database and server settings.",
            "files": ["config.py"]
        },
        {
            "name": "Data Models",
            "description": "Data models representing the application's domain entities.",
            "files": ["models/user.py", "models/post.py"]
        },
        {
            "name": "Database Layer",
            "description": "Database connection and query execution functionality.",
            "files": ["database.py"]
        },
        {
            "name": "API Layer",
            "description": "API endpoints and route handlers for the application.",
            "files": ["api/__init__.py", "api/routes.py"]
        }
    ]
    
    # Mock relationships
    relationships = {
        "Application Entry Point": ["Configuration", "Data Models", "Database Layer", "API Layer"],
        "Configuration": [],
        "Data Models": [],
        "Database Layer": ["Configuration"],
        "API Layer": ["Data Models", "Database Layer"]
    }
    
    # Mock ordered chapters
    ordered_chapters = [
        "Configuration",
        "Data Models",
        "Database Layer",
        "API Layer",
        "Application Entry Point"
    ]
    
    # Create the mock data dictionary
    mock_data = {
        "repo_name": "mock-app",
        "repo_dir": "/mock/repo",
        "files": files,
        "repo_metadata": {
            "url": "https://github.com/mock/mock-app",
            "name": "mock-app",
            "description": "A mock application for testing EnlightenAI",
            "stars": 100,
            "forks": 20,
            "issues": 5,
            "last_commit": "2023-01-01"
        },
        "web_content": {
            "https://mock-app.com/docs": {
                "title": "Mock App Documentation",
                "content": "This is the documentation for the Mock App."
            }
        },
        "abstractions": abstractions,
        "relationships": relationships,
        "ordered_chapters": ordered_chapters
    }
    
    return mock_data
