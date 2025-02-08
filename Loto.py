from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from random import sample
import uuid
import random
import string

# Créer une instance de l'application Flask
app = Flask(__name__)

# Configuration de la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loto1.db'  # Base de données SQLite locale
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Désactive les notifications de modification pour des raisons de performance
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Clé secrète utilisée par Flask pour les sessions

# Initialisation de l'extension SQLAlchemy pour la gestion de la base de données
db = SQLAlchemy(app)

# Activation des contraintes de clé étrangère dans SQLite
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Active les contraintes de clé étrangère pour SQLite, qui ne sont pas activées par défaut
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")  # Active les clés étrangères
        cursor.close()

# Définition des modèles de données pour la base

# Modèle représentant un joueur
class Joueur(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Clé primaire
    pseudo = db.Column(db.String(50), unique=True, nullable=False)  # Pseudo du joueur (doit être unique)
    numeros = db.Column(db.String(50))  # Numéros joués par le joueur
    etoiles = db.Column(db.String(50))  # Étoiles jouées par le joueur
    participation = db.Column(db.Boolean, default=True)  # Indique si le joueur participe
    password = db.Column(db.String(100), nullable=False)  # Mot de passe du joueur
    numero_unique = db.Column(db.String(50), unique=True, nullable=False)  # Identifiant unique
    resultats = db.relationship('Resultat', backref='joueur', cascade='all, delete-orphan')  # Relation avec les résultats

# Modèle représentant un tirage
class Tirage(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Clé primaire
    numeros = db.Column(db.String(50))  # Numéros gagnants du tirage
    etoiles = db.Column(db.String(50))  # Étoiles gagnantes du tirage
    montant = db.Column(db.Float, nullable=False)  # Montant total à distribuer
    resultats = db.relationship('Resultat', backref='tirage', cascade='all, delete-orphan')  # Relation avec les résultats

class Resultat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tirage_id = db.Column(db.Integer, db.ForeignKey('tirage.id', ondelete='CASCADE'), nullable=False)
    joueur_id = db.Column(db.Integer, db.ForeignKey('joueur.id', ondelete='CASCADE'), nullable=False)
    bons_numeros = db.Column(db.Integer)
    bonnes_etoiles = db.Column(db.Integer)
    gain = db.Column(db.Float)
    classement = db.Column(db.Integer)
    proximity_score = db.Column(db.Integer)  




# Routes de l'application

# Route pour la page d'accueil (inscription d'un joueur)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Récupère les données du formulaire
        pseudo = request.form['pseudo']
        password = request.form['password']

        # Validation de la longueur du pseudo
        if len(pseudo) < 2 or len(pseudo) > 15:
            flash("Le pseudo doit comporter entre 2 et 15 caractères.", "error")
            return redirect(url_for('index'))

        # Vérifie si le pseudo est déjà utilisé
        if Joueur.query.filter_by(pseudo=pseudo).first():
            flash("Pseudo déjà pris, veuillez choisir un autre.", "error")
            return redirect(url_for('index'))

        participation = True  # Par défaut, le joueur participe
        auto_generate = 'auto_generate' in request.form  # Si les numéros sont générés automatiquement

        if auto_generate:
            # Génère automatiquement des numéros et des étoiles
            numeros = ','.join(map(str, sorted(sample(range(1, 50), 5))))
            etoiles = ','.join(map(str, sorted(sample(range(1, 10), 2))))
        else:
            # Récupère les numéros et étoiles sélectionnés manuellement
            selected_numbers = request.form.getlist('numeros')
            selected_stars = request.form.getlist('etoiles')
            if len(selected_numbers) != 5 or len(selected_stars) != 2:
                flash("Veuillez sélectionner 5 numéros et 2 étoiles.", "error")
                return redirect(url_for('index'))
            numeros = ','.join(map(str, sorted(map(int, selected_numbers))))
            etoiles = ','.join(map(str, sorted(map(int, selected_stars))))

        # Crée un nouvel objet Joueur
        numero_unique = str(uuid.uuid4())  # Génère un identifiant unique
        nouveau_joueur = Joueur(
            pseudo=pseudo,
            numeros=numeros,
            etoiles=etoiles,
            participation=participation,
            password=password,
            numero_unique=numero_unique
        )

        # Ajoute le joueur à la base de données
        db.session.add(nouveau_joueur)
        db.session.commit()

        flash("Inscription réussie !", "success")
        return redirect(url_for('index'))

    # Affiche la page d'inscription
    return render_template('index.html')

# Route pour modifier les numéros d'un joueur
@app.route('/modifier_numeros/<int:id>', methods=['GET', 'POST'])
def modifier_numeros(id):
    joueur = Joueur.query.get_or_404(id)  # Récupère le joueur ou renvoie une erreur 404
    if request.method == 'POST':
        selected_numbers = request.form.getlist('numeros')
        selected_stars = request.form.getlist('etoiles')
        if len(selected_numbers) != 5 or len(selected_stars) != 2:
            flash("Veuillez sélectionner exactement 5 numéros et 2 étoiles.", "error")
            return redirect(url_for('modifier_numeros', id=joueur.id))
        
        # Met à jour les numéros et étoiles du joueur
        joueur.numeros = ','.join(map(str, sorted(map(int, selected_numbers))))
        joueur.etoiles = ','.join(map(str, sorted(map(int, selected_stars))))
        db.session.commit()

        flash("Les numéros et étoiles ont été mis à jour.", "success")
        return redirect(url_for('joueurs'))

    # Affiche la page de modification des numéros
    joueur_numeros = list(map(int, joueur.numeros.split(',')))
    joueur_etoiles = list(map(int, joueur.etoiles.split(',')))
    return render_template('modifier_numeros.html', joueur=joueur, joueur_numeros=joueur_numeros, joueur_etoiles=joueur_etoiles)

# Route pour supprimer un joueur
@app.route('/supprimer_joueur/<int:id>', methods=['GET', 'POST'])
def supprimer_joueur(id):
    joueur = Joueur.query.get_or_404(id)  # Récupère le joueur ou renvoie une erreur 404
    if request.method == 'POST':
        # Supprime le joueur de la base de données
        db.session.delete(joueur)
        db.session.commit()
        flash("Joueur supprimé avec succès.", "success")
        return redirect(url_for('joueurs'))
    
    # Affiche la page de confirmation de suppression
    return render_template('supprimer_joueur.html', joueur=joueur)

# Route pour simuler des joueurs
@app.route('/simuler_joueurs', methods=['POST'])
def simuler_joueurs():
    try:
        # Récupère le nombre de joueurs à générer
        nb_joueurs = int(request.form['nb_joueurs'])
        if nb_joueurs < 1:
            flash("Le nombre de joueurs doit être au moins de 1.", "error")
            return redirect(url_for('joueurs'))
    except ValueError:
        flash("Veuillez entrer un nombre valide.", "error")
        return redirect(url_for('joueurs'))

    # Limite à 100 le nombre de joueurs générés
    if nb_joueurs > 100:
        nb_joueurs = 100
        flash("Le nombre de joueurs a été limité à 100.", "info")
    
    participation = True  # Par défaut, les joueurs participent

    # Génère les joueurs simulés
    last_joueur = Joueur.query.order_by(Joueur.id.desc()).first()
    start_index = last_joueur.id + 1 if last_joueur else 1

    # Boucle pour générer les joueurs avec des numéros et étoiles aléatoires
    for i in range(start_index, start_index + nb_joueurs):
        pseudo = f"Joueur_{i}"
        numeros = ','.join(map(str, sorted(sample(range(1, 50), 5))))  # Génère 5 numéros aléatoires
        etoiles = ','.join(map(str, sorted(sample(range(1, 10), 2))))  # Génère 2 étoiles aléatoires
        password = pseudo
        numero_unique = str(uuid.uuid4())  # Génère un identifiant unique

        # Crée un nouveau joueur simulé
        joueur = Joueur(
            pseudo=pseudo,
            numeros=numeros,
            etoiles=etoiles,
            participation=participation,
            password=password,
            numero_unique=numero_unique
        )
        db.session.add(joueur)  # Ajoute chaque joueur à la base de données

    db.session.commit()  # Sauvegarde tous les changements dans la base
    flash(f"{nb_joueurs} joueurs ont été générés avec succès.", "success")
    return redirect(url_for('joueurs'))  # Redirige vers la page des joueurs

# Route pour lancer un tirage
@app.route('/tirage', methods=['GET', 'POST'])
def lancer_tirage():
    if request.method == 'POST':
        try:
            montant = float(request.form['montant'])  # Récupère le montant total du tirage
        except (ValueError, KeyError):
            flash("Veuillez entrer un montant valide.", "error")
            return redirect(url_for('lancer_tirage'))

        # Vérifie si la génération automatique des numéros et étoiles est activée
        auto_generate = 'auto_generate' in request.form

        if auto_generate:
            # Génère automatiquement des numéros et étoiles gagnants
            numeros_gagnants = sorted(sample(range(1, 50), 5))
            etoiles_gagnantes = sorted(sample(range(1, 10), 2))
        else:
            # Récupère les numéros et étoiles sélectionnés manuellement dans le formulaire
            try:
                numeros_gagnants = list(map(int, request.form.getlist('numeros')))
                etoiles_gagnantes = list(map(int, request.form.getlist('etoiles')))
                if len(numeros_gagnants) != 5 or len(etoiles_gagnantes) != 2:
                    flash("Veuillez sélectionner exactement 5 numéros et 2 étoiles.", "error")
                    return redirect(url_for('lancer_tirage'))
            except ValueError:
                flash("Une erreur est survenue lors de la sélection des numéros et des étoiles.", "error")
                return redirect(url_for('lancer_tirage'))

        # Crée un nouveau tirage
        tirage = Tirage(
            numeros=','.join(map(str, numeros_gagnants)),
            etoiles=','.join(map(str, etoiles_gagnantes)),
            montant=montant
        )
        db.session.add(tirage)
        db.session.commit()

        # Récupère les joueurs qui participent au tirage
        joueurs = Joueur.query.filter_by(participation=True).all()

        if not joueurs:
            flash("Aucun joueur participant n'est inscrit pour ce tirage.", "info")
            return redirect(url_for('lancer_tirage'))

        # Pour chaque joueur, calcule les résultats
        for joueur in joueurs:
            joueur_numeros = list(map(int, joueur.numeros.split(',')))
            joueur_etoiles = list(map(int, joueur.etoiles.split(',')))
            bons_numeros = len(set(joueur_numeros) & set(numeros_gagnants))
            bonnes_etoiles = len(set(joueur_etoiles) & set(etoiles_gagnantes))

            # Calcule le score de proximité
            proximity_score_numeros = calculate_proximity(joueur_numeros, numeros_gagnants)
            proximity_score_etoiles = calculate_proximity(joueur_etoiles, etoiles_gagnantes)
            proximity_score = proximity_score_numeros + proximity_score_etoiles

            # Crée un résultat pour chaque joueur
            resultat = Resultat(
                tirage_id=tirage.id,
                joueur_id=joueur.id,
                bons_numeros=bons_numeros,
                bonnes_etoiles=bonnes_etoiles,
                proximity_score=proximity_score
            )
            db.session.add(resultat)

        db.session.commit()

        # Classe les joueurs par nombre de bons numéros, bonnes étoiles et score de proximité
        resultats = Resultat.query.filter_by(tirage_id=tirage.id).all()
        resultats_sorted = sorted(
            resultats,
            key=lambda x: (
                x.bons_numeros,
                x.bonnes_etoiles,
                -x.proximity_score
            ),
            reverse=True
        )

        # Attribution des gains aux gagnants (maximum 10 gagnants)
        pourcentages_base = {1: 40, 2: 20, 3: 12, 4: 7, 5: 6, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1}
        max_gagnants = 10
        gagnants_attribues = 0
        classement = 1
        index = 0

        winners = []
        total_prize = montant  # Montant total à distribuer
        rank_percentages = pourcentages_base  # Dictionnaire des pourcentages par rang

        # Attribue les gains en fonction du classement
        while index < len(resultats_sorted) and gagnants_attribues < max_gagnants:
            current_result = resultats_sorted[index]
            current_score = (
                current_result.bons_numeros,
                current_result.bonnes_etoiles,
                -current_result.proximity_score
            )
            tied_players = [current_result]
            index += 1

            # Cherche les joueurs ayant le même score
            while index < len(resultats_sorted):
                next_result = resultats_sorted[index]
                next_score = (
                    next_result.bons_numeros,
                    next_result.bonnes_etoiles,
                    -next_result.proximity_score
                )
                if next_score == current_score:
                    tied_players.append(next_result)
                    index += 1
                else:
                    break

            if gagnants_attribues + len(tied_players) > max_gagnants:
                tied_players = tied_players[:max_gagnants - gagnants_attribues]

            for res in tied_players:
                res.classement = classement
                winners.append(res)

            gagnants_attribues += len(tied_players)
            classement += 1

        num_winners = len(winners)

        if num_winners < 10:
            total_percentage = sum(rank_percentages.get(res.classement, 0.0) for res in winners)

            if total_percentage == 0:
                raise ValueError("Erreur : La somme des pourcentages des gagnants est égale à zéro.")

            for res in winners:
                pourcentage = rank_percentages.get(res.classement, 0.0)
                res.gain = (total_prize * (pourcentage / total_percentage))
                db.session.commit()
        else:
            for res in winners:
                pourcentage = rank_percentages.get(res.classement, 0.0)
                res.gain = (pourcentage / 100) * total_prize
                db.session.commit()

        while index < len(resultats_sorted):
            res = resultats_sorted[index]
            res.gain = 0
            res.classement = "Non classé"
            db.session.commit()
            index += 1

        # Prépare les résultats à afficher
        resultats_display = []
        for res in resultats_sorted:
            joueur = Joueur.query.get(res.joueur_id)
            resultats_display.append({
                'joueur_id': joueur.id,
                'pseudo': joueur.pseudo,
                'numeros': joueur.numeros.split(','),
                'etoiles': joueur.etoiles.split(','),
                'bons_numeros': res.bons_numeros,
                'bonnes_etoiles': res.bonnes_etoiles,
                'gain': round(res.gain if res.gain else 0, 2),
                'classement': res.classement if res.classement else 'Non classé'
            })

        return render_template('tirage.html',
                               numeros_gagnants=numeros_gagnants,
                               etoiles_gagnantes=etoiles_gagnantes,
                               resultats=resultats_display,
                               montant=montant)

    return render_template("lancer_tirage.html")




# Route pour supprimer tous les joueurs de la base de données
@app.route('/supprimer_tous_les_joueurs', methods=['POST'])
def supprimer_tous_les_joueurs():
    try:
        Joueur.query.delete()  # Supprime tous les joueurs
        db.session.commit()  # Valide la suppression
        flash("Tous les joueurs ont été supprimés avec succès.", "success")
    except Exception as e:
        db.session.rollback()  # Annule en cas d'erreur
        flash(f"Une erreur est survenue lors de la suppression : {str(e)}", "error")
    return redirect(url_for('joueurs'))

# Route pour réclamer un gain par un joueur
@app.route('/reclamer/<int:joueur_id>', methods=['GET', 'POST'])
def reclamer_gain(joueur_id):
    joueur = Joueur.query.get_or_404(joueur_id)
    if request.method == 'POST':
        password = request.form['password']  # Récupère le mot de passe du formulaire

        # Vérifie si le mot de passe est correct
        if joueur.password == password:
            resultat = Resultat.query.filter_by(joueur_id=joueur.id).order_by(Resultat.id.desc()).first()
            if resultat and resultat.gain > 0:
                flash(f"Félicitations, vous remportez {round(resultat.gain)} € ! Veuillez vous rendre à la FDJ avec votre code secret : {joueur.numero_unique}.", "success")
                return redirect(url_for('afficher_resultats'))
            else:
                flash("Vous n'avez aucun gain à réclamer.", "info")
                return redirect(url_for('afficher_resultats'))
        else:
            flash("Mot de passe incorrect, veuillez réessayer.", "error")

    return render_template('reclamer_gain.html', joueur=joueur)

# Route pour modifier la participation d'un joueur
@app.route('/modifier_participation/<int:id>', methods=['POST'])
def modifier_participation(id):
    joueur = db.session.get(Joueur, id)
    if joueur is None:
        abort(404)
    joueur.participation = not joueur.participation  # Inverse la participation
    db.session.commit()
    return redirect(url_for('joueurs'))

# Route pour afficher la liste des joueurs
@app.route('/joueurs', methods=['GET', 'POST'])
def joueurs():
    joueurs = Joueur.query.all()  # Récupère tous les joueurs de la base de données
    return render_template('joueurs.html', joueurs=joueurs)  # Affiche la page avec la liste des joueurs

def calculate_proximity(player_grille, winning_grille):
    """
    Calcule l'écart entre les numéros incorrects de la grille du joueur et les numéros incorrects de la grille gagnante,
    en laissant les numéros corrects intacts et sans réutiliser les numéros gagnants déjà comparés.
    """
    correct_numbers = set(player_grille) & set(winning_grille)
    player_incorrect = [num for num in player_grille if num not in correct_numbers]
    winning_incorrect = [num for num in winning_grille if num not in correct_numbers]
    
    proximity_score = 0
    
    for num in player_incorrect:
        if winning_incorrect:
            closest = min(winning_incorrect, key=lambda x: abs(x - num))
            proximity_score += abs(num - closest)
            winning_incorrect.remove(closest)
    
    return proximity_score




# Route pour afficher les résultats du dernier tirage
@app.route('/resultats')
def afficher_resultats():
    tirage = Tirage.query.order_by(Tirage.id.desc()).first()  # Récupère le dernier tirage
    if not tirage:
        return "Aucun tirage n'a été effectué."  # Si aucun tirage n'a eu lieu, renvoie un message

    # Récupère tous les résultats liés à ce tirage
    resultats = Resultat.query.filter_by(tirage_id=tirage.id).all()
    resultats_display = []
    
    # Prépare les résultats pour l'affichage
    for res in resultats:
        joueur = Joueur.query.get(res.joueur_id)
        resultats_display.append({
            'joueur_id': joueur.id,
            'pseudo': joueur.pseudo,
            'numeros': joueur.numeros.split(','),  # Conversion des numéros en liste
            'etoiles': joueur.etoiles.split(','),
            'bons_numeros': res.bons_numeros,
            'bonnes_etoiles': res.bonnes_etoiles,
            'gain': round(res.gain if res.gain else 0, 2),
            'classement': res.classement if res.classement else 'Non classé'
        })

    # Trie les résultats par classement (les joueurs non classés en dernier)
    resultats_display = sorted(resultats_display, key=lambda x: (x['classement'] if isinstance(x['classement'], int) else float('inf')))
    
    # Convertit les numéros et étoiles gagnants du tirage en listes d'entiers
    numeros_gagnants = list(map(int, tirage.numeros.split(',')))
    etoiles_gagnantes = list(map(int, tirage.etoiles.split(',')))

    # Affiche la page des résultats
    return render_template('resultats.html',
                           numeros_gagnants=numeros_gagnants,
                           etoiles_gagnantes=etoiles_gagnantes,
                           resultats=resultats_display)

# Point d'entrée de l'application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crée toutes les tables dans la base de données au démarrage
    app.run(debug=True)  # Lancer l'application en mode debug
