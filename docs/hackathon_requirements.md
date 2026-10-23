# Hackathon requirements and verification checklist

Source: supplied Code Coogs Hackathon Survival Guide, read from its DOCX body on October 23, 2026. This is the supplied guide, not a separately verified Challenge 2 rules document. All implementation tasks below remain planned unless explicitly marked inspected.

## Guide-supported items

| Guide item | Implementation task / deliverable | Status |
|---|---|---|
| Five-hour event; phased game plan | Time-box audit, data, prototype, interface and submission | Planned |
| Short problem statement and why it matters | README and buyer-focused pitch | Planned |
| Data sources; assumptions or simulated data labeled | Data manifest, methodology, limitations | Initial supplied-file inspection complete |
| Working notebook or public demo URL, plus source | Streamlit public URL and accessible source, following project preference | Planned |
| Methods, evidence/results and limitations | Evaluation reports and methodology view | Planned |
| Team member names | README and submission material | Names needed |
| 2–3 minute demo plan | presentation/demo_script.md | Planned |
| No API keys/private credentials on GitHub | Ignore rules, environment example, secret review | Planned |
| Data in repository only if license permits | Verify terms before redistributing | Unverified |
| Simple baseline and held-out evaluation in guide examples | Baseline comparisons and valid data/time splits | Planned |
| Clear data-driven explanation valued over appearance | Real metrics, provenance and limitations in demo | Planned |

## Available paths and project choices

The guide allows Kaggle/Colab notebook sharing without a website, a Streamlit dashboard deployed from GitHub, or a React/Next.js app with hosting. These are alternatives. Streamlit plus a public URL is the project's chosen target from the master prompt, not a universal event mandate. The guide recommends GitHub for the Streamlit workflow and asks for source code; it does not establish a universal requirement for a public GitHub repository.

The guide's hurricane example is illustrative and does not replace the requested housing project. Tool/tutorial mentions are suggestions, not an exhaustive list of permitted tools.

## Not specified in the supplied guide

- Challenge 2 topic constraints or formal acceptance criteria.
- Numeric judging rubric or scoring weights.
- Calendar submission deadline, timezone or submission portal.
- Required file formats, repository visibility or naming convention.
- Mandatory five-model comparisons or minimum AI model count.
- External dataset eligibility and licensing rules beyond permission-aware sharing.
- Restrictions on external APIs, pretrained models or paid tools.
- Required host or platform beyond the alternative suggested workflows.
- Team size, eligibility, attendance and participation rules.
- Whether pre-event code is permitted and what must be built during the event.
- Formal presentation duration; the guide requests a 2–3 minute demo plan.

Request the separate challenge brief and deadline. Absence of a restriction in this guide is not proof that no other official rules exist.

## Project-brief requirements, additional to the guide

| Project brief | Planned implementation / evidence |
|---|---|
| Property listings plus ZHVI | Schema audit; immutable raw inputs; provenance manifest |
| Houston/Houstonia/South Houston, Texas | Exact city-label filter; report missing Houstonia TX |
| Historical integration | Validated ZIP joins and date-availability policy |
| Five regression models, two feature sets | Identical partitions, train-only tuning, dollar MAE selection |
| Pricing classification | Out-of-sample pseudo-labels; transparent configurable rule; honest optional five-classifier comparison |
| Five forecast methods; 6/12 months | Multiple chronological origins; naive comparison; calibrated intervals when possible |
| Five chatbot configurations where feasible | Fixed factual evaluation; record unavailable methods; deterministic fallback |
| SHAP | Actual selected-model explanations; units and causal limits stated |
| Property map and ZIP choropleth | Valid points, credible boundaries, documented ZIP/ZCTA approximation |
| Historical versus latest values | Explicit dates and separate estimates/adjustments/forecasts |
| Seven application sections | Overview, map, property, forecasts, assistant, evaluations, methodology |
| Colab-compatible pipeline | Configurable paths, reproducible entry point, exported serving artifacts |
| Public deployment | Account/repository configuration and verified public URL |
| Tests, reports and presentation | Integrity tests, user journey, measured results, demo and judge Q&A |
| Optional recommendation system | Only after core deliverables; historical examples clearly labeled |

See implementation_draft.md for sequencing, acceptance criteria, methodological safeguards and open questions.
