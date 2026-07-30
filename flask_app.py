"""
OJEDDREH — Site institutionnel
Python + Flask (compatible PythonAnywhere)

Lancement en local :  python flask_app.py
Puis ouvrir http://127.0.0.1:5000
"""
import functools
import json
import os
import urllib.request
import uuid
from datetime import datetime

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-uniquement-a-changer-en-production")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Dossier privé (hors /static) pour les pièces jointes des candidatures :
# jamais servi publiquement, uniquement via la route admin authentifiée /admin/fichiers/<...>
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
EXTENSIONS_AUTORISEES = {"pdf", "jpg", "jpeg", "png", "doc", "docx"}

# Mot de passe de l'espace réservé aux organisateurs (à définir sur PythonAnywhere
# dans l'onglet Web > Environment variables, ne jamais laisser la valeur par défaut en ligne)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ojeddreh-admin")

# Notification par e-mail à chaque formulaire reçu, via l'API HTTP de Brevo
# (le SMTP classique est bloqué sur le plan gratuit PythonAnywhere, mais api.brevo.com
# est sur leur liste blanche). À définir sur PythonAnywhere dans l'onglet Web > Environment variables :
# BREVO_API_KEY (clé API Brevo) et EMAIL_EXPEDITEUR (adresse validée comme expéditeur dans Brevo).
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
EMAIL_NOTIFICATION = os.environ.get("EMAIL_NOTIFICATION", "ojeddreh@gmail.com")
EMAIL_EXPEDITEUR = os.environ.get("EMAIL_EXPEDITEUR", EMAIL_NOTIFICATION)
NOM_EXPEDITEUR = os.environ.get("NOM_EXPEDITEUR", "Site OJEDDREH")

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


# ---------- Utilitaires de données ----------
def lire_json(nom_fichier, defaut=None):
    """Lit un fichier JSON du dossier data/."""
    if defaut is None:
        defaut = []
    chemin = os.path.join(DATA_DIR, nom_fichier)
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return defaut


def ajouter_json(nom_fichier, entree):
    """Ajoute une soumission (avec un identifiant unique) dans un fichier JSON du dossier data/."""
    chemin = os.path.join(DATA_DIR, nom_fichier)
    liste = lire_json(nom_fichier, [])
    entree = dict(entree)
    entree["id"] = uuid.uuid4().hex[:10]
    entree["recu_le"] = datetime.now().isoformat()
    liste.append(entree)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)
    return entree["id"]


def maj_evaluation(nom_fichier, id_cible, evaluation):
    """Enregistre/écrase la note interne d'une soumission identifiée par id_cible."""
    chemin = os.path.join(DATA_DIR, nom_fichier)
    liste = lire_json(nom_fichier, [])
    trouve = False
    for entree in liste:
        if entree.get("id") == id_cible:
            entree["evaluation"] = evaluation
            trouve = True
            break
    if trouve:
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(liste, f, ensure_ascii=False, indent=2)
    return trouve


def cases_cochees(donnees, prefixe, options):
    """Reconstruit une liste de valeurs cochées à partir de cases nommées 'prefixe_option'."""
    return [libelle for cle, libelle in options if str(donnees.get(f"{prefixe}_{cle}", "")).strip()]


def sauver_fichier(fichier, sous_dossier):
    """Sauvegarde un fichier envoyé (pièce jointe) dans uploads/<sous_dossier>/ et renvoie son chemin relatif."""
    if not fichier or not fichier.filename:
        return None
    extension = fichier.filename.rsplit(".", 1)[-1].lower() if "." in fichier.filename else ""
    if extension not in EXTENSIONS_AUTORISEES:
        return None
    nom_sur = f"{uuid.uuid4().hex[:12]}_{secure_filename(fichier.filename)}"
    dossier = os.path.join(UPLOAD_DIR, sous_dossier)
    os.makedirs(dossier, exist_ok=True)
    fichier.save(os.path.join(dossier, nom_sur))
    return f"{sous_dossier}/{nom_sur}"


def formater_donnees(donnees, exclure=()):
    """Formate un dict de soumission en texte lisible pour le corps d'un e-mail."""
    lignes = []
    for cle, valeur in donnees.items():
        if cle in exclure or valeur in (None, "", []):
            continue
        if isinstance(valeur, list):
            valeur = ", ".join(str(v) for v in valeur)
        lignes.append(f"- {cle} : {valeur}")
    return "\n".join(lignes) if lignes else "(aucune donnée)"


def envoyer_notification(sujet, corps):
    """Envoie un e-mail d'alerte via l'API Brevo ; n'interrompt jamais le formulaire en cas d'échec."""
    if not BREVO_API_KEY:
        print("[notification e-mail] BREVO_API_KEY non configurée — e-mail non envoyé.", flush=True)
        return
    charge_utile = json.dumps({
        "sender": {"name": NOM_EXPEDITEUR, "email": EMAIL_EXPEDITEUR},
        "to": [{"email": EMAIL_NOTIFICATION}],
        "subject": sujet,
        "textContent": corps,
    }).encode("utf-8")
    requete = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=charge_utile,
        method="POST",
        headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json", "accept": "application/json"},
    )
    try:
        urllib.request.urlopen(requete, timeout=10)
    except Exception as erreur:
        print(f"[notification e-mail] Échec de l'envoi : {erreur}", flush=True)


def date_fr(valeur):
    """Transforme '2026-01-15' en '15 janvier 2026'."""
    try:
        d = datetime.strptime(str(valeur)[:10], "%Y-%m-%d")
        return f"{d.day} {MOIS[d.month - 1]} {d.year}"
    except (ValueError, TypeError):
        return valeur


# Rend date_fr et l'année courante disponibles dans tous les gabarits
app.jinja_env.filters["date_fr"] = date_fr


@app.context_processor
def variables_globales():
    return {"annee": datetime.now().year}


# ================= PAGES =================
@app.route("/")
def accueil():
    return render_template("index.html", active="accueil")


@app.route("/a-propos")
def a_propos():
    return render_template("a-propos.html", active="apropos")


DOMAINES = [
    ("01", "Développement du leadership",
     "Former une nouvelle génération de leaders éthiques, responsables et capables d'influencer positivement leurs communautés."),
    ("02", "Développement personnel",
     "Renforcer les soft skills, la confiance en soi, la communication, la discipline et la gestion du temps."),
    ("03", "Entrepreneuriat & innovation",
     "Accompagner la création d'entreprises innovantes et soutenir les porteurs de projets."),
    ("04", "Agrobusiness & agriculture",
     "Promouvoir une agriculture moderne, rentable, résiliente et orientée vers les chaînes de valeur."),
    ("05", "Innovation technologique",
     "Développer les compétences numériques, l'IA et les technologies au service du développement."),
    ("06", "Formation & employabilité",
     "Renforcer les compétences techniques pour améliorer l'accès à l'emploi et à l'auto-emploi."),
    ("07", "Éducation & recherche",
     "Soutenir l'excellence académique, la recherche appliquée et la production de connaissances utiles."),
    ("08", "Engagement citoyen",
     "Promouvoir la participation citoyenne, la bonne gouvernance, la transparence et le leadership communautaire."),
    ("09", "Développement économique local",
     "Encourager les initiatives créatrices d'emplois, les PME, les coopératives et les économies locales."),
    ("10", "Environnement & climat",
     "Sensibiliser aux enjeux climatiques et promouvoir la protection de l'environnement et des pratiques durables."),
    ("11", "Inclusion sociale",
     "Favoriser l'égalité des chances et la participation active des jeunes et des femmes."),
    ("12", "Partenariats stratégiques",
     "Développer des collaborations avec universités, entreprises, ONG et partenaires internationaux."),
]


@app.route("/domaines")
def domaines():
    return render_template("domaines.html", domaines=DOMAINES, active="domaines")


@app.route("/programmes")
def programmes():
    return render_template("programmes.html", active="programmes")


@app.route("/partenaires")
def partenaires():
    return render_template("partenaires.html", active="")


@app.route("/don")
def don():
    return render_template("don.html", active="")


DEPARTEMENTS_ORGANISATION = [
    "Direction Réseau et Partenariats",
    "Direction Communication et Médias",
    "Direction Finance et Administration",
    "Direction Formation et Encadrement",
    "Direction Agriculture et Environnement",
    "Direction Culture et Développement Communautaire",
    "Direction Entrepreneuriat et Innovation",
    "Direction Technologie et Transformation Digitale",
]


@app.route("/membre")
def membre():
    return render_template("membre.html", active="", departements=DEPARTEMENTS_ORGANISATION)


@app.route("/contact")
def contact():
    return render_template("contact.html", active="contact")


@app.route("/actualites")
def actualites():
    items = lire_json("actualites.json")
    items.sort(key=lambda a: a.get("date", ""), reverse=True)
    return render_template("actualites.html", items=items, active="actualites")


@app.route("/publications")
def publications():
    return render_template("publications.html",
                           items=lire_json("publications.json"),
                           active="publications")


# ================= API FORMULAIRES =================
def traiter(nom_fichier, champs_requis, message_succes, sujet_notification):
    """Valide les champs, enregistre la soumission puis notifie l'équipe par e-mail."""
    donnees = request.get_json(silent=True) or request.form.to_dict()
    for champ in champs_requis:
        if not str(donnees.get(champ, "")).strip():
            return jsonify(ok=False,
                           message=f"Le champ « {champ} » est requis."), 400
    try:
        ajouter_json(nom_fichier, donnees)
        try:
            sujet = sujet_notification.format(**{k: donnees.get(k, "") for k in donnees})
        except (KeyError, IndexError):
            sujet = sujet_notification
        envoyer_notification(sujet, formater_donnees(donnees))
        return jsonify(ok=True, message=message_succes)
    except Exception:
        return jsonify(ok=False,
                       message="Erreur serveur. Réessayez plus tard."), 500


@app.route("/api/contact", methods=["POST"])
def api_contact():
    return traiter("submissions_contact.json",
                   ["prenom", "nom", "email", "message"],
                   "Merci ! Votre message a bien été envoyé.",
                   "Nouveau message de contact — {prenom} {nom}")


@app.route("/api/membre", methods=["POST"])
def api_membre():
    # main.js envoie en multipart dès qu'une pièce jointe est choisie, sinon en JSON
    est_multipart = (request.content_type or "").startswith("multipart/form-data")
    donnees = request.form.to_dict() if est_multipart else (request.get_json(silent=True) or {})

    champs_requis = ["nom_complet", "email", "telephone", "departement"]
    for champ in champs_requis:
        if not str(donnees.get(champ, "")).strip():
            return jsonify(ok=False, message=f"Le champ « {champ} » est requis."), 400

    donnees["langues"] = cases_cochees(donnees, "langue", [
        ("creole", "Créole"), ("francais", "Français"),
        ("anglais", "Anglais"), ("espagnol", "Espagnol"),
    ])
    donnees["creneaux_disponibles"] = cases_cochees(donnees, "creneau", [
        ("matin", "Matin"), ("apres_midi", "Après-midi"),
        ("soir", "Soir"), ("weekend", "Week-end"),
    ])

    if est_multipart:
        donnees["fichier_piece_identite"] = sauver_fichier(request.files.get("piece_identite"), "membre")
        donnees["fichier_photo_identite"] = sauver_fichier(request.files.get("photo_identite"), "membre")
        donnees["fichier_cv"] = sauver_fichier(request.files.get("cv"), "membre")
        donnees["fichier_lettre_motivation"] = sauver_fichier(request.files.get("lettre_motivation"), "membre")

    try:
        ajouter_json("submissions_membre.json", donnees)
        exclure = {"langue_creole", "langue_francais", "langue_anglais", "langue_espagnol",
                   "creneau_matin", "creneau_apres_midi", "creneau_soir", "creneau_weekend",
                   "accepte_charte", "accepte_ethique", "accepte_confidentialite", "certification",
                   "fichier_piece_identite", "fichier_photo_identite", "fichier_cv", "fichier_lettre_motivation"}
        corps = (f"Nouvelle candidature d'adhésion reçue sur le site OJEDDREH.\n\n"
                 f"{formater_donnees(donnees, exclure)}\n\n"
                 f"Voir le dossier et le noter : {url_for('admin_candidatures', _external=True)}")
        envoyer_notification(f"Nouvelle candidature d'adhésion — {donnees.get('nom_complet', '')}", corps)
        return jsonify(ok=True, message="Merci ! Votre candidature a bien été reçue. Notre comité l'examinera prochainement.")
    except Exception:
        return jsonify(ok=False, message="Erreur serveur. Réessayez plus tard."), 500


@app.route("/api/atelier", methods=["POST"])
def api_atelier():
    donnees = request.get_json(silent=True) or request.form.to_dict()

    champs_requis = ["nom_prenom", "email", "telephone"]
    for champ in champs_requis:
        if not str(donnees.get(champ, "")).strip():
            return jsonify(ok=False, message=f"Le champ « {champ} » est requis."), 400

    donnees["centres_interet"] = cases_cochees(donnees, "interet", [
        ("dev_personnel", "Développement personnel"), ("leadership", "Leadership"),
        ("agriculture", "Agriculture"), ("entrepreneuriat_agricole", "Entrepreneuriat agricole"),
        ("agrobusiness", "Agro-business"), ("innovation", "Innovation"),
        ("gestion_projet", "Gestion de projet"),
    ])

    try:
        ajouter_json("submissions_atelier.json", donnees)
        exclure = {"interet_dev_personnel", "interet_leadership", "interet_agriculture",
                   "interet_entrepreneuriat_agricole", "interet_agrobusiness", "interet_innovation",
                   "interet_gestion_projet", "accepte_engagement"}
        corps = (f"Nouvelle inscription à un atelier reçue sur le site OJEDDREH.\n\n"
                 f"{formater_donnees(donnees, exclure)}\n\n"
                 f"Voir le dossier et le noter : {url_for('admin_ateliers', _external=True)}")
        envoyer_notification(f"Nouvelle inscription atelier — {donnees.get('nom_prenom', '')}", corps)
        return jsonify(ok=True, message="Merci ! Votre inscription à l'atelier a bien été reçue.")
    except Exception:
        return jsonify(ok=False, message="Erreur serveur. Réessayez plus tard."), 500


@app.route("/api/partenaire", methods=["POST"])
def api_partenaire():
    return traiter("submissions_partenaire.json",
                   ["organisation", "contact", "email", "message"],
                   "Merci ! Votre demande de partenariat a bien été envoyée.",
                   "Nouvelle demande de partenariat — {organisation}")


@app.route("/api/don", methods=["POST"])
def api_don():
    return traiter("submissions_don.json", ["nom", "email"],
                   "Merci pour votre intention de don ! Nous vous recontacterons pour finaliser.",
                   "Nouvelle intention de don — {nom}")


@app.route("/api/newsletter", methods=["POST"])
def api_newsletter():
    return traiter("submissions_newsletter.json", ["email"],
                   "Merci ! Vous êtes inscrit·e à notre infolettre.",
                   "Nouvelle inscription infolettre — {email}")


# ================= ESPACE RÉSERVÉ (notation des candidatures reçues) =================
def connexion_requise(vue):
    @functools.wraps(vue)
    def enveloppe(*args, **kwargs):
        if not session.get("admin_connecte"):
            return redirect(url_for("admin_connexion", suivant=request.path))
        return vue(*args, **kwargs)
    return enveloppe


GRILLE_CANDIDATURE = [
    ("motivation", "Motivation", 20), ("leadership", "Leadership", 15),
    ("competences_techniques", "Compétences techniques", 15), ("disponibilite", "Disponibilité", 15),
    ("travail_equipe", "Travail en équipe", 10), ("vision_communautaire", "Vision communautaire", 10),
    ("references", "Références", 5),
]
GRILLE_ATELIER = [
    ("motivation", "Motivation", 20), ("pertinence_profil", "Pertinence du profil", 20),
    ("disponibilite", "Disponibilité", 20), ("potentiel_entrepreneurial", "Potentiel entrepreneurial", 20),
    ("impact_attendu", "Impact attendu", 20),
]


@app.route("/admin/connexion", methods=["GET", "POST"])
def admin_connexion():
    erreur = None
    if request.method == "POST":
        if request.form.get("mot_de_passe") == ADMIN_PASSWORD:
            session["admin_connecte"] = True
            return redirect(request.args.get("suivant") or url_for("admin_accueil"))
        erreur = "Mot de passe incorrect."
    return render_template("admin/connexion.html", erreur=erreur)


@app.route("/admin/deconnexion")
def admin_deconnexion():
    session.pop("admin_connecte", None)
    return redirect(url_for("admin_connexion"))


@app.route("/admin")
@connexion_requise
def admin_accueil():
    candidatures = lire_json("submissions_membre.json")
    ateliers = lire_json("submissions_atelier.json")
    return render_template("admin/accueil.html",
                           nb_candidatures=len(candidatures), nb_ateliers=len(ateliers))


@app.route("/admin/candidatures")
@connexion_requise
def admin_candidatures():
    candidatures = lire_json("submissions_membre.json")
    candidatures.sort(key=lambda c: c.get("recu_le", ""), reverse=True)
    return render_template("admin/candidatures.html", candidatures=candidatures, grille=GRILLE_CANDIDATURE)


@app.route("/admin/candidatures/<id_candidature>/noter", methods=["POST"])
@connexion_requise
def admin_noter_candidature(id_candidature):
    evaluation = {cle: request.form.get(cle, "") for cle, _, _ in GRILLE_CANDIDATURE}
    evaluation["decision"] = request.form.get("decision", "")
    evaluation["departement_attribue"] = request.form.get("departement_attribue", "")
    evaluation["fonction_proposee"] = request.form.get("fonction_proposee", "")
    evaluation["notes"] = request.form.get("notes", "")
    evaluation["evalue_le"] = datetime.now().isoformat()
    maj_evaluation("submissions_membre.json", id_candidature, evaluation)
    return redirect(url_for("admin_candidatures"))


@app.route("/admin/ateliers")
@connexion_requise
def admin_ateliers():
    inscriptions = lire_json("submissions_atelier.json")
    inscriptions.sort(key=lambda c: c.get("recu_le", ""), reverse=True)
    return render_template("admin/ateliers.html", inscriptions=inscriptions, grille=GRILLE_ATELIER)


@app.route("/admin/ateliers/<id_inscription>/noter", methods=["POST"])
@connexion_requise
def admin_noter_atelier(id_inscription):
    evaluation = {cle: request.form.get(cle, "") for cle, _, _ in GRILLE_ATELIER}
    evaluation["decision"] = request.form.get("decision", "")
    evaluation["notes"] = request.form.get("notes", "")
    evaluation["evalue_le"] = datetime.now().isoformat()
    maj_evaluation("submissions_atelier.json", id_inscription, evaluation)
    return redirect(url_for("admin_ateliers"))


@app.route("/admin/fichiers/<path:chemin_relatif>")
@connexion_requise
def admin_fichier(chemin_relatif):
    return send_from_directory(UPLOAD_DIR, chemin_relatif)


# ---------- Page 404 ----------
@app.errorhandler(404)
def page_introuvable(e):
    return render_template("404.html", active=""), 404


if __name__ == "__main__":
    app.run(debug=True)
