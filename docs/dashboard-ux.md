# Dashboard UX principles

The pilot dashboard uses a deliberately small information architecture:

1. **Optimizasyon** — the primary workflow and recommended production schedule.
2. **Tüketim analizi** — upload one meter file and understand the site's load profile.
3. **Dönem karşılaştırması** — compare baseline and reporting periods.

## Interface principles

- One clear page title and one sentence explaining the purpose.
- Three task-oriented destinations; no nested menu maze.
- Consistent spacing, restrained blue accent, high-contrast typography, and simple metric cards.
- Technical terms are explained in context rather than exposed as navigation labels.
- Upload controls appear next to the workflow that consumes their data.
- Warnings distinguish modeled estimates from measured outcomes.
- Mobile layouts collapse cleanly; the pilot remains a local Streamlit app.

## Safety and scope

This visual refresh does not add authentication, tenant isolation, persistent customer storage,
or device control. Do not deploy the pilot publicly or process confidential customer data
until those controls are implemented and reviewed.
