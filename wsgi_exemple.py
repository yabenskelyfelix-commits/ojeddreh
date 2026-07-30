# ============================================================
#  EXEMPLE de fichier WSGI pour PythonAnywhere
# ------------------------------------------------------------
#  NE PAS téléverser ce fichier tel quel.
#  Sur PythonAnywhere, allez dans l'onglet "Web", cliquez sur le lien
#  du fichier WSGI (ex. /var/www/VOTRENOM_pythonanywhere_com_wsgi.py),
#  EFFACEZ tout son contenu et collez les lignes ci-dessous
#  en remplaçant VOTRENOM par votre nom d'utilisateur PythonAnywhere.
# ============================================================

import sys

# Chemin vers le dossier qui contient flask_app.py
chemin = '/home/VOTRENOM/ojeddreh'
if chemin not in sys.path:
    sys.path.insert(0, chemin)

from flask_app import app as application  # noqa
