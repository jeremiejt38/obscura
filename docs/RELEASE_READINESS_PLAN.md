# Plan complet de release multiplateforme — Obscura

> **Statut :** plan de travail. Aucune version `1.0.0` ne doit être publiée tant que les critères de sortie correspondants ne sont pas validés.

## 1. Objectif

Obscura doit fournir une application de bureau installable sur Linux, Windows et macOS qui masque localement les données sensibles présentes dans les captures d’écran. La release doit préserver les principes suivants :

- l’image et l’OCR ne sont jamais envoyés à un service réseau ;
- le presse-papiers et les dossiers sont surveillés seulement si l’utilisateur l’autorise ;
- les fichiers source sont conservés par défaut ;
- une modification destructive requiert une option explicite ;
- l’utilisateur peut installer, lancer, comprendre les prérequis et désinstaller le produit sans manipuler le code source.

## 2. État constaté

### Capacités déjà présentes localement

- OCR local Tesseract, règles de détection et règles personnalisées.
- Masquage noir, floutage et pixellisation ; floutage prévu comme défaut pour les nouvelles configurations.
- Surveillance du presse-papiers et d’un dossier ; résultats copiés ou écrits selon les réglages.
- Application PySide6 en zone de notification avec configuration persistante, démarrage automatique et notifications.
- Mise à jour intégrée préparée : découverte d’une GitHub Release, vérification SHA-256 et remplacement du binaire empaqueté.
- Tests automatisés de configuration, moteur, watcher et mise à jour ; dernière validation locale : 13 tests passent.
- Workflows CI et releases prévus pour Linux, Windows et macOS.

### État de publication

Les changements décrits ci-dessus sont actuellement locaux et non commités. Le dépôt distant contient encore la base `v0.1.0`. Les workflows ne peuvent pas être considérés actifs avant leur commit, leur push et une exécution GitHub Actions vérifiée.

### Risques connus

- L’application de tray doit encore être validée manuellement sur GNOME/Wayland ; un warning Qt/Wayland a été observé sans blocage confirmé.
- Tesseract est aujourd’hui une dépendance système. PyInstaller peut empaqueter Python et PySide6, mais ne garantit pas un OCR Tesseract ni les langues installés sur la machine cible.
- Les binaires Windows et macOS non signés peuvent être bloqués ou avertis par SmartScreen et Gatekeeper.
- La mise à jour automatique doit être testée depuis une release installée, sur chaque plateforme qui la supporte.

## 3. Stratégie de versions

| Version | But | Public | Exigence minimale |
| --- | --- | --- | --- |
| `v0.2.0` | Release de test multiplateforme | Mainteneur et testeurs informés | CI verte, artefacts produits, Tesseract documenté, smoke tests manuels |
| `v0.3.x` | Stabilisation | Testeurs élargis | Corrections des retours, parcours installation/retrait testés |
| `v1.0.0` | Première stable | Utilisateurs finaux | Tous les critères de sortie `1.0` validés, décision explicite du mainteneur |
| `v1.x` | Améliorations compatibles | Utilisateurs finaux | Régressions couvertes et même niveau de sécurité |

Une release `1.0.0` est une décision explicite : une convention de version ne doit jamais la créer automatiquement.

## 4. Périmètre des releases

### Inclus dans `v0.2.0`

- Application de tray et CLI `obscura`.
- OCR local de texte avec langues française et anglaise lorsque les données Tesseract correspondantes sont installées.
- Catégories de données sensibles, y compris IPv4 disponible mais désactivée par défaut.
- Floutage par défaut, pixellisation et masquage noir comme choix explicites.
- Surveillance opt-in du presse-papiers et des dossiers.
- Configuration persistante, notification, démarrage automatique et vérification de mise à jour.
- Artifacts GitHub Releases pour Linux, Windows et macOS, accompagnés de checksums SHA-256.

### Exclu de `v0.2.0`

- Détection de visage et de nom par modèle local optionnel.
- Tesseract automatiquement embarqué dans les binaires, tant que la stratégie de licences, poids et mise à jour n’est pas validée.
- Signature/notarisation payante ou automatisée Windows/macOS.
- Synchronisation, traitement cloud ou compte en ligne.
- Modification automatique de fichiers sources sans activation explicite.

### Cible `v1.0.0`

Le périmètre exact de `v1.0.0` sera figé après les retours de `v0.2.x`. Le minimum est une installation et une expérience de base claires sur chaque OS annoncé, avec limites connues documentées et sans défaut critique de confidentialité, perte de données ou blocage de tray.

## 5. Décisions à prendre avant tout packaging définitif

### 5.1 Distribution de Tesseract

Choisir une stratégie unique ou une stratégie par plateforme.

| Option | Avantages | Coûts / risques | Décision à prendre |
| --- | --- | --- | --- |
| Prérequis système documenté | Rapide, léger, licences simples | Installation moins fluide, OCR absent si oubli | Recommandé pour `v0.2.0` |
| Détection + assistant | Clarifie immédiatement le problème | Demande une UX dédiée et tests OS | Recommandé avant `v1.0.0` |
| Tesseract inclus dans les artefacts | Installation autonome | Taille, licences, données de langues, maintenance, builds OS | À étudier après validation utilisateur |
| Installateur dépendant de gestionnaire système | Intégration naturelle | Différent pour chaque OS | Possible pour les canaux Linux futurs |

Décisions nécessaires : langues incluses, chemins de recherche, message en cas d’absence, lien vers les instructions officielles, comportement lorsque seule une des deux langues est disponible.

### 5.2 Format par plateforme

| Plateforme | Format `v0.2.0` possible | Format stable préférable | Validation requise |
| --- | --- | --- | --- |
| Linux | Binaire PyInstaller autonome | AppImage, paquet `.deb`, Flatpak ou paquet de distribution selon cible | X11 + Wayland, tray, OCR, permissions, lancement |
| Windows | `.exe` PyInstaller | Installateur signé (MSI/NSIS/Inno Setup) | SmartScreen, Tesseract, tray, démarrage auto, désinstallation |
| macOS | Binaire PyInstaller | `.app` signé et notarized, éventuellement `.dmg` | Gatekeeper, architecture, permissions, tray, Tesseract |

Ne pas annoncer un installateur natif si seul un binaire brut est livré. Le README et la release doivent appeler chaque artifact par son nom exact.

### 5.3 Signature et réputation

- **Windows** : déterminer si un certificat de signature est disponible. Sans signature, documenter l’avertissement SmartScreen et ne pas demander de contourner des protections sans explication.
- **macOS** : déterminer l’accès à un compte Apple Developer. Sans signature/notarisation, Gatekeeper doit être traité comme une limitation connue de la release de test.
- **Linux** : décider ultérieurement du mécanisme de confiance des paquets et dépôts ; le checksum est le minimum pour un binaire téléchargé.

### 5.4 Mise à jour intégrée

La mise à jour interne est un confort, pas une condition de publication `v0.2.0`. Elle ne doit être activée pour une plateforme que lorsque le cycle complet a été testé : découverte, téléchargement, checksum, remplacement, redémarrage, reprise après échec et restauration manuelle.

## 6. Plan d’exécution

## Phase A — Stabiliser le code local

### A.1 Revue du diff

- [ ] Examiner chaque fichier modifié et non suivi.
- [ ] Séparer les changements en ensembles cohérents : moteur/configuration, desktop/tray, updates, packaging/CI, documentation/standards et tests.
- [ ] Vérifier qu’aucun screenshot, secret, fichier de configuration personnel, cache, binaire, `.venv` ou sortie de build ne sera commit.
- [ ] Vérifier les conventions KSP : `main` stable, commits atomiques et Conventional Commits.

### A.2 Tests automatisés

- [x] Exécuter la suite locale avec environnement isolé : `uv run --with pytest python -m pytest`.
- [ ] Exécuter `python -m py_compile obscura/*.py` dans l’environnement de release Python 3.12.
- [ ] Ajouter une couverture pour chaque correctif introduit pendant la stabilisation.
- [ ] Vérifier les cas de défauts : floutage par défaut, IPv4 désactivée par défaut, sources non remplacées, règles désactivées et valeurs de configuration invalides.
- [ ] Vérifier les comportements d’erreur : image non lisible, Tesseract absent, langue OCR absente, dossier inaccessible, presse-papiers indisponible et échec réseau de vérification de version.

### A.3 Revue du tray et Wayland

- [ ] Reproduire le warning Qt avec heure, environnement (`XDG_SESSION_TYPE`, version Qt, desktop environment) et séquence exacte.
- [ ] Vérifier que le warning n’empêche ni l’icône, ni le menu, ni les notifications, ni l’ouverture des réglages.
- [ ] Vérifier que les résultats des workers sont tous livrés au thread graphique avant toute modification d’interface.
- [ ] Si le warning produit un dysfonctionnement, écrire un test de non-régression possible ou une procédure manuelle précise avant correction.
- [ ] Ne pas masquer un warning sans avoir établi son origine et son impact.

**Sortie de phase A :** tests verts, diff propre, aucun problème bloquant observé en tray Linux.

## Phase B — Validation manuelle Linux

Effectuer sur le poste cible et consigner la version de l’OS, la session X11/Wayland, la version Tesseract et le backend clipboard.

### B.1 Installation et lancement

- [ ] Créer un environnement propre ou utiliser le binaire généré.
- [ ] Vérifier le message et la documentation lorsque Tesseract manque.
- [ ] Installer Tesseract et les langues nécessaires selon la documentation.
- [ ] Lancer `obscura-desktop` et vérifier l’icône SVG.
- [ ] Vérifier le double-clic, le menu contextuel, l’ouverture/fermeture des réglages et le bouton Quitter.
- [ ] Redémarrer l’application et vérifier la persistance des réglages.

### B.2 Fonctionnalités de confidentialité

- [ ] Copier une image de test contenant un e-mail, téléphone, secret simulé, carte de test et IPv4.
- [ ] Vérifier que les catégories actives sont floutées.
- [ ] Vérifier qu’une IPv4 seule n’est pas masquée par défaut.
- [ ] Activer explicitement IPv4 et vérifier qu’elle est alors masquée.
- [ ] Comparer floutage, pixellisation et noir ; vérifier les rayons et tailles configurés.
- [ ] Vérifier qu’une image sans données sensibles ne remplace pas inutilement le presse-papiers.
- [ ] Vérifier que les images et leurs données ne quittent pas la machine à l’exception de la vérification de mises à jour explicitement configurée.

### B.3 Dossiers et fichiers

- [ ] Surveiller un dossier temporaire, puis déposer des PNG/JPEG/WebP de test.
- [ ] Vérifier la sortie, le suffixe `-obscura`, l’arborescence de sortie et l’ignorance des propres résultats.
- [ ] Vérifier le mode récursif et le comportement sur fichier en cours d’écriture.
- [ ] Vérifier que le remplacement de source demande une confirmation et reste désactivé par défaut.
- [ ] Vérifier les erreurs : dossier supprimé, image corrompue, manque d’espace simulé si possible.

### B.4 Cycle de vie

- [ ] Vérifier l’activation/désactivation de chaque moniteur depuis le menu.
- [ ] Vérifier le démarrage automatique puis sa désactivation.
- [ ] Vérifier que Quitter arrête les threads de surveillance sans laisser de processus en arrière-plan.
- [ ] Vérifier la reprise après redémarrage de session.

**Sortie de phase B :** une grille de résultats Linux complétée, anomalies classées bloquantes ou non bloquantes.

## Phase C — Intégrer et vérifier GitHub Actions

### C.1 Commits

Créer seulement après la phase A, avec des commits atomiques. Exemple de découpage à adapter au diff réel :

1. `feat(desktop): add configurable tray redaction workflow`
2. `feat(engine): add persistent detection and output settings`
3. `feat(updater): add checksum-verified release updates`
4. `build: add cross-platform binary release workflow`
5. `test: cover configuration engine and update flows`
6. `docs: document desktop installation privacy and release process`

Ne pas forcer ce découpage si les dépendances de code ne le permettent pas ; chaque commit doit rester testable.

### C.2 Push et CI

- [ ] Pousser les commits sur une branche de travail ou sur `main` selon le workflow approuvé.
- [ ] Vérifier la CI sur Ubuntu, Windows et macOS avec Python 3.9 et 3.12.
- [ ] Pour chaque échec, identifier si le problème vient de dépendances, plateforme, test non déterministe ou packaging.
- [ ] Corriger avec un test de régression lorsque raisonnable.
- [ ] Ne pas préparer de Release PR tant que les jobs essentiels sont rouges.

### C.3 Contrôle de la release automation

- [ ] Vérifier que Release Please reconnaît les commits et ouvre une Release PR cohérente.
- [ ] Vérifier la version proposée et le changelog.
- [ ] Vérifier que le tag de release déclenche exactement le workflow de binaires.
- [ ] Vérifier les permissions GitHub `contents: write` et `pull-requests: write` sans élargissement inutile.

**Sortie de phase C :** CI entièrement verte, Release PR prête et relue.

## Phase D — Produire `v0.2.0`

### D.1 Préparation

- [ ] Relire README, CHANGELOG, SECURITY, CONTRIBUTING et documentation de tests.
- [ ] Décrire clairement le statut de release de test, les plateformes ciblées et les limites Tesseract/signature.
- [ ] Vérifier que `pyproject.toml` est la source de version et que `obscura/__init__.py` est synchronisé par Release Please.
- [ ] Vérifier qu’aucune promesse de support ne dépasse les tests effectués.

### D.2 Publication

- [ ] Examiner puis merger la Release PR `v0.2.0`.
- [ ] Attendre la création du tag annoté et le déclenchement du workflow de release.
- [ ] Vérifier les trois artifacts et leurs fichiers `.sha256` dans la GitHub Release.
- [ ] Télécharger chaque artifact dans un emplacement propre et vérifier son checksum hors GitHub Actions.
- [ ] Vérifier le contenu de la release : version, changelog, notes de sécurité et procédure d’installation.

### D.3 Smoke tests des artifacts

| Test | Linux | Windows | macOS |
| --- | --- | --- | --- |
| Téléchargement + SHA-256 | [ ] | [ ] | [ ] |
| Lancement du binaire | [ ] | [ ] | [ ] |
| Signal de sécurité OS compris/documenté | [ ] | [ ] | [ ] |
| Tesseract détecté ou aide affichée | [ ] | [ ] | [ ] |
| Icône et menu tray | [ ] | [ ] | [ ] |
| Réglages persistants | [ ] | [ ] | [ ] |
| Presse-papiers | [ ] | [ ] | [ ] |
| Dossier surveillé | [ ] | [ ] | [ ] |
| Fichier de sortie non destructif | [ ] | [ ] | [ ] |
| Mise à jour : découverte seulement | [ ] | [ ] | [ ] |

Si macOS ou Windows ne sont pas accessibles physiquement, une CI verte ne remplace pas ce tableau : la release est alors explicitement limitée à un test technique sur ces plateformes.

**Sortie de phase D :** `v0.2.0` publiable comme release de test, avec limites déclarées.

## Phase E — Itération et préparation de `v1.0.0`

### E.1 Retours et incidents

- [ ] Centraliser les problèmes de lancement, OCR, clipboard, notifications, performance, installation et mise à jour.
- [ ] Prioriser les bugs de confidentialité et perte de données avant toute amélioration d’interface.
- [ ] Ajouter des tests reproduisant les bugs corrigés.
- [ ] Refaire les smoke tests après chaque modification packaging ou updater.

### E.2 Installation utilisable

- [ ] Décider et implémenter la stratégie Tesseract retenue.
- [ ] Ajouter une détection de dépendances et un message d’aide clair avant le premier traitement si Tesseract est absent.
- [ ] Évaluer les formats natifs : AppImage/paquet Linux, installateur Windows, `.app`/`.dmg` macOS.
- [ ] Définir proprement l’installation, la mise à jour et la désinstallation de chaque format.
- [ ] Décider de la signature Windows et Apple, ou documenter précisément leur absence.

### E.3 Mise à jour fiable

- [ ] Tester une mise à jour de `v0.2.0` vers `v0.2.1` dans une installation empaquetée.
- [ ] Simuler : checksum invalide, réseau indisponible, téléchargement interrompu, fichier non remplaçable et redémarrage interrompu.
- [ ] Vérifier que le binaire précédent est conservé ou récupérable après échec.
- [ ] Évaluer séparément Linux, Windows et macOS ; désactiver l’installation automatique sur une plateforme si elle n’est pas fiable.

### E.4 Accessibilité et UX

- [ ] Vérifier clavier, contraste, textes FR/EN, taille des fenêtres et libellés de catégories.
- [ ] Vérifier que les actions à risque sont explicites : remplacement de source, démarrage automatique, update et choix de répertoires.
- [ ] Vérifier que la configuration IPv4 désactivée et floutage par défaut sont visibles et compréhensibles.

## 7. Critères de sortie `v1.0.0`

Tous les critères suivants sont obligatoires sauf dérogation écrite et assumée dans les notes de release.

### Produit et confidentialité

- [ ] Aucune donnée d’image ou OCR n’est transmise à un service réseau par le traitement normal.
- [ ] Les défauts de configuration sont sûrs : floutage, IPv4 désactivée, non-remplacement des sources et moniteurs contrôlables.
- [ ] Les erreurs OCR et les limites sont documentées ; l’utilisateur est invité à vérifier une image avant partage.
- [ ] Les catégories, règles personnalisées, langues et sorties configurées correspondent au comportement réel.

### Stabilité

- [ ] Tous les tests automatisés passent sur la matrice CI annoncée.
- [ ] Les tests manuels minimaux des trois plateformes annoncées sont consignés.
- [ ] Aucune anomalie bloquante tray, clipboard, configuration, sortie, Tesseract ou crash connu n’est ouverte.
- [ ] Le démarrage, l’arrêt et la désinstallation sont vérifiés sur chaque format distribué.

### Distribution et sécurité

- [ ] Chaque artifact possède une version exacte et un checksum publié.
- [ ] Les prérequis Tesseract sont installables, détectés et documentés.
- [ ] Le niveau de signature et ses éventuels avertissements OS sont clairement communiqués.
- [ ] La mise à jour automatique est testée sur les plateformes où elle est proposée ; les autres proposent un chemin manuel sûr.
- [ ] README, release notes, changelog, licence, sécurité et contribution sont cohérents avec le binaire publié.

### Maintenabilité

- [ ] Une procédure de reproduction de build est documentée.
- [ ] La procédure de rollback de release et d’update est documentée.
- [ ] Le support de chaque OS annoncé est réaliste et maintenable.
- [ ] Le mainteneur approuve explicitement la publication `v1.0.0`.

## 8. Commandes de validation de référence

Les commandes exactes peuvent évoluer avec l’outillage, mais chaque release doit conserver un équivalent fonctionnel :

```bash
uv run --with pytest python -m pytest
uv run python -m py_compile obscura/*.py
uv build
```

Pour une exécution locale de l’application :

```bash
uv run obscura-desktop
```

Le packaging officiel est produit par GitHub Actions depuis un tag validé ; les builds manuels ne doivent pas remplacer la validation des artifacts publiés.

## 9. Journal de décision

Utiliser cette section pour conserver les décisions qui changent le périmètre de release.

| Date | Décision | Motif | Conséquence |
| --- | --- | --- | --- |
| 2026-07-26 | Floutage par défaut | Rendu souhaité pour les données sensibles | Nouvelles configurations en mode `blur` |
| 2026-07-26 | IPv4 désactivée par défaut | Éviter le masquage excessif des adresses locales | Catégorie activable manuellement |
| À définir | Stratégie Tesseract | Installation utilisateur et taille des artifacts | Conditionne le parcours `v1.0.0` |
| À définir | Signature Windows/macOS | Avertissements de sécurité et confiance | Conditionne la qualité de distribution stable |

## 10. Première action recommandée

Terminer la grille de validation manuelle Linux du tray, puis réaliser la revue du diff et les commits atomiques. Une fois ces commits poussés, la CI multiplateforme donnera la première information objective sur la capacité réelle de produire `v0.2.0`.
