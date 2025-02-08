import unittest
from flask_testing import TestCase
from Loto import app, db, Joueur, Tirage, Resultat
import uuid

class TestLotoApp(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loto1.db'  # Utilisation de SQLite en mémoire
        app.config['SECRET_KEY'] = 'test_secret_key'
        app.config['WTF_CSRF_ENABLED'] = False  # Désactivation de CSRF pour les tests
        return app

    def setUp(self):
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('index.html')

    def test_player_registration(self):
        data = {
            'pseudo': 'testplayer',
            'password': 'testpassword',
            'numeros': ['1', '2', '3', '4', '5'],
            'etoiles': ['1', '2']
        }
        response = self.client.post('/', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Inscription réussie', response.data.decode('utf-8'))

        joueur = Joueur.query.filter_by(pseudo='testplayer').first()
        self.assertIsNotNone(joueur)
        self.assertEqual(joueur.numeros, '1,2,3,4,5')
        self.assertEqual(joueur.etoiles, '1,2')

    def test_auto_generated_numbers_registration(self):
        data = {
            'pseudo': 'autoplayer',
            'password': 'autopassword',
            'auto_generate': 'on'
        }
        response = self.client.post('/', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Inscription réussie', response.data.decode('utf-8'))

        joueur = Joueur.query.filter_by(pseudo='autoplayer').first()
        self.assertIsNotNone(joueur)
        self.assertIsNotNone(joueur.numeros)
        self.assertIsNotNone(joueur.etoiles)

    def test_duplicate_pseudo_registration(self):
        joueur = Joueur(
            pseudo='duplicateplayer',
            password='password',
            numeros='1,2,3,4,5',
            etoiles='1,2',
            numero_unique=str(uuid.uuid4())
        )
        db.session.add(joueur)
        db.session.commit()

        data = {
            'pseudo': 'duplicateplayer',
            'password': 'newpassword',
            'numeros': ['6', '7', '8', '9', '10'],
            'etoiles': ['3', '4']
        }
        response = self.client.post('/', data=data, follow_redirects=True)
        self.assertIn('Pseudo déjà pris', response.data.decode('utf-8'))

    def test_modify_player_numbers(self):
        joueur = Joueur(
            pseudo='modplayer',
            password='password',
            numeros='1,2,3,4,5',
            etoiles='1,2',
            numero_unique=str(uuid.uuid4())
        )
        db.session.add(joueur)
        db.session.commit()

        data = {
            'numeros': ['6', '7', '8', '9', '10'],
            'etoiles': ['3', '4']
        }
        response = self.client.post(f'/modifier_numeros/{joueur.id}', data=data, follow_redirects=True)
        self.assertIn('Les numéros et étoiles ont été mis à jour', response.data.decode('utf-8'))

        joueur = Joueur.query.get(joueur.id)
        self.assertEqual(joueur.numeros, '6,7,8,9,10')
        self.assertEqual(joueur.etoiles, '3,4')

    def test_delete_player(self):
        joueur = Joueur(
            pseudo='delplayer',
            password='password',
            numeros='1,2,3,4,5',
            etoiles='1,2',
            numero_unique=str(uuid.uuid4())
        )
        db.session.add(joueur)
        db.session.commit()

        response = self.client.post(f'/supprimer_joueur/{joueur.id}', follow_redirects=True)
        self.assertIn('Joueur supprimé avec succès', response.data.decode('utf-8'))

        joueur = Joueur.query.get(joueur.id)
        self.assertIsNone(joueur)




    def test_simulate_players(self):
        data = {'nb_joueurs': '5'}
        response = self.client.post('/simuler_joueurs', data=data, follow_redirects=True)
        self.assertIn('5 joueurs ont été générés avec succès', response.data.decode('utf-8'))

        joueurs = Joueur.query.all()
        self.assertEqual(len(joueurs), 5)

    def test_delete_all_players(self):
        joueur1 = Joueur(
            pseudo='player1',
            password='password1',
            numeros='1,2,3,4,5',
            etoiles='1,2',
            participation=True,
            numero_unique=str(uuid.uuid4())
        )
        joueur2 = Joueur(
            pseudo='player2',
            password='password2',
            numeros='6,7,8,9,10',
            etoiles='3,4',
            participation=True,
            numero_unique=str(uuid.uuid4())
        )
        db.session.add_all([joueur1, joueur2])
        db.session.commit()

        response = self.client.post('/supprimer_tous_les_joueurs', follow_redirects=True)
        self.assertIn('Tous les joueurs ont été supprimés avec succès', response.data.decode('utf-8'))

        joueurs = Joueur.query.all()
        self.assertEqual(len(joueurs), 0)


if __name__ == '__main__':
    unittest.main()
