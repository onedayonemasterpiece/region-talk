# Security policy

- Repository, Kaggle kernels, Kaggle datasets, workflow artifacts and operator reports are private by default.
- No Telegram session, Google key, Supabase key, Kaggle token, VK token, database credential or decrypted secret may be committed or printed.
- Production workflows fail closed when the shared Google AI limiter is unavailable.
- A secret-leak scan is a release gate for every Kaggle run bundle and every GitHub artifact.
- Suspected disclosure requires immediate rotation, invalidation of affected Kaggle dataset versions where possible, incident documentation and a replay audit.
- Full procedures: `docs/security-and-secrets.md`.
