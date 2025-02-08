# tests/conftest.py

import pytest
from app import app, db

@pytest.fixture(scope='module')
def test_client():
    # Configuration de l'application pour les tests
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Base de données en mémoire
    app.config['WTF_CSRF_ENABLED'] = False  # Désactiver CSRF pour les tests si vous utilisez WTForms

    # Crée un client de test
    with app.test_client() as testing_client:
        with app.app_context():
            db.create_all()
        yield testing_client  # Fournit le client de test aux tests

        # Après les tests, nettoie la base de données
        with app.app_context():
            db.session.remove()
            db.drop_all()
