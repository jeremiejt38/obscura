# Subset de validation Obscura (CH-04)

Corpus minimal à tester avant chaque release — une image par catégorie de pattern sensible, générée synthétiquement (pas de vraies données).

| Catégorie | Chaîne de test | Attendu |
|---|---|---|
| email | `user@example.com` | détecté |
| iban | `FR1420041010050500013M02606` | détecté |
| phone | `06 12 34 56 78` | détecté |
| ipv4 | `203.0.113.7` | détecté (depuis v0.2.x) |
| bearer | `Bearer eyJhbGci...` | détecté |
| ssh_key | `ssh-ed25519 AAAA...` | détecté |
| webhook | `https://discord.com/api/webhooks/1/x` | détecté |
| credit_card | `4111 1111 1111 1111` | détecté |
| api_key | `sk-AbCdEf1234567890` | détecté |
| private_key | `-----BEGIN PRIVATE KEY-----` | détecté |
| **faux positif** | `The version 1.2.3 is fine` | NON détecté |

Procédure : `pytest tests/test_redactor.py` (couvre les catégories) + test visuel sur captures réelles anonymisées. Une régression = blocage release.
