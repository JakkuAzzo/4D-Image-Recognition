# OSINT Engine Next Steps (Deferred)

- Normalize platform results (twitter/x, instagram, linkedin) into a common schema.
- Add robustness for rate limits and CAPTCHAs (do not automate sites without permissions).
- Integrate reverse image results with vector DB metadata and 4D models.
- Expand tests to cover presence/absence of optional deps.

This work is optional and deferred as requested. The current `/osint-data` endpoint already guards against fake data and falls back safely.
