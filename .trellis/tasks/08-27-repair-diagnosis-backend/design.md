# Design

Add one repair router, one repair model module, and one additive migration. Keep SQLAlchemy queries simple: exact normalized PN + product type + `approved`; then product family (only when present) and product type + failure type. Do not add vector search for the current small dataset. Depend on existing verified-user/admin dependencies, returning FastAPI errors in existing style.
