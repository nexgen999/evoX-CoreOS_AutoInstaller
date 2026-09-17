# 🚀 evoX CoreOS & WebUI - Guide d'installation et de configuration

Bienvenue dans l'installateur automatique **evoX CoreOS & WebUI** ! Ce dépôt vous permet de déployer et de configurer automatiquement un environnement web complet pour evoX.

---

## 📋 Prérequis : Création du Personal Access Token (PAT)

Afin d'autoriser l'action GitHub Actions à créer/mettre à jour les workflows et les fichiers de votre dépôt, vous devez obligatoirement configurer un **Personal Access Token (PAT)**.

### 1️⃣ Générer le Token GitHub (PAT)
1. Cliquez sur votre **photo de profil** (en haut à droite de GitHub) ➔ **Settings**.
2. Dans le menu latéral de gauche, descendez tout en bas et cliquez sur **Developer settings**.
3. Allez dans **Personal access tokens** ➔ **Tokens (classic)**.
4. Cliquez sur **Generate new token** ➔ **Generate new token (classic)**.
5. Complétez les champs :
   * **Note** : `evoX Installer Token`
   * **Expiration** : Sélectionnez la durée souhaitée (ou `No expiration`).
   * **Scopes (Autorisations)** : **Cochez la case `workflow`** (cela sélectionnera automatiquement `repo` et les accès requis).
6. Cliquez sur le bouton vert **Generate token** en bas de page.
7. ⚠️ **Copiez immédiatement le token généré** (`ghp_...`). Vous ne pourrez plus le revoir par la suite.

---

### 2️⃣ Ajouter le Secret sur votre Dépôt
1. Rendez-vous sur la page de **votre dépôt d'installation** (`evoX-CoreOS-Installer_Test` ou votre fork).
2. Cliquez sur l'onglet **Settings** (du dépôt) ➔ **Secrets and variables** ➔ **Actions**.
3. Cliquez sur **New repository secret**.
4. Remplissez le formulaire :
   * **Name** : `GH_PAT`
   * **Secret** : *Collez le token copié précédemment (`ghp_...`)*
5. Cliquez sur **Add secret**.

---

## ⚙️ Configuration des Permissions du Dépôt

1. Dans les **Settings** de votre dépôt, allez dans le menu **Actions** ➔ **General**.
2. Descendez jusqu'à la section **Workflow permissions** :
   * Sélectionnez **Read and write permissions**.
   * Cochez la case **Allow GitHub Actions to create and approve pull requests**.
3. Cliquez sur **Save**.

---

## 🚀 Lancer l'installation automatique

1. Rendez-vous dans l'onglet **Actions** de votre dépôt.
2. Dans la colonne de gauche, cliquez sur **evoX Auto Installer**.
3. Cliquez sur le menu déroulant **Run workflow** ➔ puis sur le bouton vert **Run workflow**.

---

## 🛠️ Que fait l'installateur automatique ?

L'action **evoX Auto Installer** effectue automatiquement les opérations suivantes :
* 📦 **Clonage sélectif** des fichiers cibles définis dans `install-manifest.json` depuis `evoX-CoreOS` et `evoX-CoreOS-WebUI`.
* 📁 **Création de la structure de dossiers** requise (`assets/icon/`, `feed/apps/`, `feed/ffpfsc/`, `feed/payloads/`, `feed/pkg/`).
* 🔧 **Mise à jour dynamique de `web/data/config.json`** pour adapter les URLs raw, GitHub Pages et releases à votre propre nom d'utilisateur/dépôt.
* 🧹 **Auto-nettoyage** : Suppression de l'installateur et du manifeste une fois la configuration terminée.

---

## 📄 Structure de `web/data/config.json`

Le fichier `web/data/config.json` est automatiquement adapté avec vos identifiants GitHub. Les champs mis à jour dynamiquement incluent :
* `github.user`
* `github.dataRepository` & `github.webuiRepository`
* `sources.pldmgr` & `sources.json[].url`
* `sources.changelog`
* `releases.baseUrl`
* `socials[0].url`

---

## 🤝 Crédits & Communauté

* **evoX Team**
* **ItsPLK for PLDMGR**
* **Master, Mustafa, SeregonWar, maj0r, ArkSama, aldostools, VoX DoN, BX-AM, Pippo, Phoenixx, Pegasus Dev, DLPS Team**
* **All Scene Community**
