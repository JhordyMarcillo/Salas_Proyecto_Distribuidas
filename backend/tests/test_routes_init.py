"""
Tests adicionales para aumentar cobertura de app/routes/__init__.py
"""

from app import create_app
from app.routes import register_blueprints, auth_bp, rooms_bp, upload_bp


def test_register_blueprints():
    """
    Test para asegurar que los blueprints se registran correctamente
    """
    # Crear app (ya tiene blueprints registrados en create_app)
    app = create_app('testing')

    # Verificar que los blueprints están importados correctamente
    assert auth_bp is not None
    assert rooms_bp is not None
    assert upload_bp is not None

    # Verificar que los blueprints están ya registrados en la aplicación
    assert auth_bp.name in app.blueprints
    assert rooms_bp.name in app.blueprints
    assert upload_bp.name in app.blueprints


def test_import_blueprints():
    """
    Test para asegurar que los blueprints se importan correctamente
    """
    from app.routes.auth import auth_bp
    from app.routes.rooms import rooms_bp
    from app.routes.upload import upload_bp

    assert auth_bp is not None
    assert rooms_bp is not None
    assert upload_bp is not None