# Site OJEDDREH — version Python / Flask

Site institutionnel de l'**Organisation des Jeunes pour le Développement Durable
et de la Résilience Économique d'Haïti**.

Technologies : **Python + Flask + Jinja2 + CSS + JavaScript**
→ compatible **PythonAnywhere**.

---

## 🚀 Déployer sur PythonAnywhere (pas à pas)

### 1. Créer le compte
Allez sur **pythonanywhere.com** et créez un compte **Beginner (gratuit)**.
Votre site sera à l'adresse `https://VOTRENOM.pythonanywhere.com`.

### 2. Téléverser les fichiers
Onglet **Files**. Créez un dossier `ojeddreh` dans `/home/VOTRENOM/`,
puis téléversez-y tout le contenu de ce projet en respectant la structure :

```
/home/VOTRENOM/ojeddreh/
├── flask_app.py
├── requirements.txt
├── static/     (css, js, img)
├── templates/  (les pages)
└── data/       (actualites.json, publications.json, submissions_*.json)
```

> Astuce : pour aller plus vite, téléversez le fichier `.zip` puis, dans une
> console Bash de PythonAnywhere, tapez : `unzip ojeddreh-flask.zip`

### 3. Installer Flask
Onglet **Consoles** → ouvrez une console **Bash**, puis tapez :

```bash
pip3 install --user Flask
```

### 4. Créer l'application web
Onglet **Web** → **Add a new web app** → **Next** →
choisissez **Flask** → puis la version de **Python 3** proposée.

### 5. Configurer le fichier WSGI
Toujours dans l'onglet **Web**, section *Code*, cliquez sur le lien du fichier
**WSGI configuration file**. Effacez tout son contenu et collez ceci
(en remplaçant `VOTRENOM`) :

```python
import sys

chemin = '/home/VOTRENOM/ojeddreh'
if chemin not in sys.path:
    sys.path.insert(0, chemin)

from flask_app import app as application
```

Enregistrez (**Save**).

### 6. Indiquer le dossier source
Dans l'onglet **Web**, section *Code*, réglez :

- **Source code** : `/home/VOTRENOM/ojeddreh`

### 7. Déclarer les fichiers statiques
Toujours dans l'onglet **Web**, section **Static files**, ajoutez :

| URL       | Directory                            |
|-----------|--------------------------------------|
| `/static/` | `/home/VOTRENOM/ojeddreh/static/`   |

### 8. Lancer
Cliquez sur le gros bouton vert **Reload**.
Votre site est en ligne sur `https://VOTRENOM.pythonanywhere.com` 🎉

---

## ⚠️ À savoir sur le compte gratuit

- L'adresse est imposée : `VOTRENOM.pythonanywhere.com`.
  Un **nom de domaine personnalisé** (ex. `ojeddreh.org`) nécessite un plan payant.
- Les comptes gratuits doivent être **réactivés périodiquement** : un bouton
  apparaît dans l'onglet Web (« Run until 3 months from today »). Pensez-y,
  sinon le site s'arrête.
- **Bonne nouvelle** : contrairement à d'autres hébergeurs, le disque de
  PythonAnywhere est **permanent**. Les messages reçus via les formulaires
  (dossier `data/`) sont donc bien conservés.

---

## 🔄 Après chaque modification

1. Modifiez le fichier concerné (onglet **Files**, ou téléversez la nouvelle version).
2. Onglet **Web** → bouton **Reload**.

C'est tout. Les changements sont visibles immédiatement.

---

## ✏️ Modifier le contenu

| Ce que vous voulez changer   | Fichier à modifier                          |
|------------------------------|---------------------------------------------|
| Texte d'une page             | `templates/nom-de-la-page.html`             |
| Couleurs, styles             | `static/css/styles.css` (variables en haut) |
| Ajouter une actualité        | `data/actualites.json`                      |
| Ajouter une publication      | `data/publications.json`                    |
| Menu, pied de page           | `templates/partials/`                       |
| Logo, photos                 | déposer dans `static/img/`                  |

**Exemple — ajouter une actualité** dans `data/actualites.json` :

```json
{
  "titre": "Titre de l'actualité",
  "tag": "Événement",
  "date": "2026-03-10",
  "resume": "Quelques phrases de résumé."
}
```

(Attention aux virgules entre les blocs — une virgule manquante casse la page.)

---

## 💻 Tester en local (optionnel)

```bash
pip install -r requirements.txt
python flask_app.py
```
Puis ouvrez http://127.0.0.1:5000

---

## 📨 Formulaires

Les 5 formulaires (contact, adhésion, partenariat, don, infolettre) enregistrent
les données dans `data/submissions_*.json`, consultables via l'onglet **Files**.

---

## 🔜 Prochaines étapes possibles

1. **Espace d'administration** — publier les actualités depuis une page web
   protégée par mot de passe, sans toucher aux fichiers.
2. **Envoi par e-mail** des soumissions vers `ojeddreh@gmail.com`.
3. **Paiement en ligne** des dons (MonCash, PayPal).
4. **Nom de domaine** `ojeddreh.org` (nécessite un plan payant).
5. **Traductions** créole et anglais (structure FR/HT/EN déjà en place).
6. **Photos de terrain** à intégrer.

---

© 2026 OJEDDREH — Route Nationale #6, Village La Différence (EKAM), Haïti
ojeddreh@gmail.com · +509 3538 8312
