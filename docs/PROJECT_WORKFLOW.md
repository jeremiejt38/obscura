# Workflow de développement — Obscura

Obscura applique le standard partagé situé dans `/home/jerem/workspace/.devin/templates/project-standards/PROJECT_WORKFLOW.md` avec les adaptations ci-dessous.

## Branches actives

- `main` est la seule branche stable et publiable.
- Créer des branches courtes depuis `main` : `feature/<sujet>`, `fix/<sujet>`, `docs/<sujet>`, `chore/<sujet>`, `refactor/<sujet>` ou `test/<sujet>`.
- Une sous-branche `feature/<parent>/<sous-sujet>` n’est autorisée que pour isoler une expérimentation ou un sous-chantier ; elle est fusionnée puis supprimée avant la branche parente.
- Après validation, rebaser sur `main`, fusionner en fast-forward, vérifier l’intégration et supprimer les branches locale et distante.

Les branches `alpha` et `beta` ne sont pas actives. Elles pourront être créées plus tard pour maintenir des canaux de test séparés, avec les préversions `vX.Y.Z-alpha.N`, `vX.Y.Z-beta.N` et `vX.Y.Z-rc.N`.

## Commits et validation

Les commits sont atomiques, testables et écrits avec Conventional Commits : `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci` ou `chore`.

Avant tout merge : exécuter `python -m pytest`, vérifier la compilation Python si applicable, contrôler le diff et mettre à jour le README ou la roadmap lorsque l’usage, l’installation ou le périmètre changent.

## Releases

Release Please analyse les Conventional Commits de `main` et maintient une Release PR. Le mainteneur relit puis fusionne cette PR pour publier une version stable, son changelog et le tag annoté `vX.Y.Z`.

- `fix:` propose un patch.
- `feat:` propose une mineure.
- `BREAKING CHANGE:` ou `!` propose une majeure.
- Une majeure ne peut être validée ou publiée sans accord explicite du mainteneur.

**Progression :** une mineure est suivie de ses patches jusqu'à la mineure suivante.
Exemple : `1.0.0 → 1.0.1 (patch) → 1.0.2 (patch) → 1.1.0 (mineure) → 1.1.1 (patch) → …`.

Le workflow existant de release construit ensuite les binaires Linux, macOS et Windows depuis ce tag.

## Talos

Talos est actuellement désactivé car il est instable. Lorsqu’il sera réactivé explicitement, il pourra traiter des jobs isolés dans son sandbox. Tout résultat devra être récupéré, relu, testé et évalué avant intégration ; aucune modification Talos ne sera acceptée aveuglément.
