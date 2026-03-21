"""Blueprint package init"""
from .auth import auth_bp
from .admin import admin_bp
from .review import review_bp
from .media import media_bp

__all__ = ['auth_bp', 'admin_bp', 'review_bp', 'media_bp']
