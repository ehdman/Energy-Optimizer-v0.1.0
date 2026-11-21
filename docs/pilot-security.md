# Pilot security and customer data

## Current application behavior

The v0.4.0 pilot dashboard runs locally with Streamlit. It reads a JSON production scenario and CSV/XLSX meter files, then computes analyses and schedules in process memory. It has no database, customer login, tenant isolation, billing, or industrial control connection.

The fact that the current app does not intentionally save an uploaded scenario is not a complete privacy or security guarantee for a hosted environment. Hosting, proxies, logs, backups, and operator access must be reviewed before customer data is processed.

## Before any hosted customer pilot

- Require authenticated accounts and role-based access control.
- Enforce tenant isolation in every API, query, report, and file operation.
- Use HTTPS/TLS and managed secrets; never commit passwords, tokens, API keys, or customer data.
- Encrypt sensitive data at rest and in backups.
- Define retention, deletion, export, and incident response procedures contractually.
- Minimize collected data; avoid employee-level or personally identifying data unless strictly necessary.
- Validate uploaded file size, schema, numeric ranges, timestamps, and units. Current pilot limits scenario JSON to 2 MB, meter files to 10 MB, meter rows to 100,000, and planning intervals to 10,000.
- Add audit logs for access, configuration changes, exports, and approved operational actions.
- Perform dependency, application, and access-control reviews before production launch.

## Industrial safety boundary

This product currently generates decision-support recommendations only. It must not directly control machinery, PLCs, SCADA, HVAC, inverters, batteries, or EV chargers.

Any future write/control integration requires a separate threat model, independent safety interlocks, least-privilege credentials, operator approval, fail-safe behavior, rollback procedures, and site-specific engineering review. Energy cost optimization must never override process safety, product quality, equipment limits, or legal requirements.

## Customer pilot data

Before accepting customer data, agree in writing:
- the purpose and authorized users;
- the exact data fields and time range;
- the storage location and retention period;
- who can access the data;
- how the customer can retrieve or request deletion;
- whether the data may be used to improve the product or train models (default: no secondary use without explicit agreement).
