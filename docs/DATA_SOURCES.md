# Data sources

Verified on 2026-11-03. This is engineering due diligence, not legal advice. The machine-readable record is `ml/data/source_registry.json` (checked by `ml/data/validate_registry.py` and a CI job); this page explains the decisions.

## How each source was checked

Each registry entry says how its terms were read (`license.verification.method`):

- **official_page_fetched**: the official terms page was read in full.
- **official_page_via_search_snippet**: excerpts of the official page were read, not the whole page. The unread parts are listed as open tasks below.
- **dataset_card_via_search_snippet** and similar: a dataset card or README excerpt was read. A dataset card states what the compiler claims, which is not proof of rights in the underlying text.

## Decisions at a glance

| Source | Role | Status | Condition that matters most |
|---|---|---|---|
| MedlinePlus health topics and test info | corpus | **approved** | Public-domain areas only; cite "Courtesy of MedlinePlus from the National Library of Medicine" |
| MedlinePlus encyclopedia, drug monographs, images | corpus | **rejected** | Copyrighted; ingesting them needs a vendor licence |
| CDC web content | corpus | conditional | Mostly public domain; allowlist pages, exclude images and third-party material |
| WHO publications | corpus | conditional | CC BY-NC-SA 3.0 IGO: non-commercial only, adaptations share-alike |
| NHS website | corpus | conditional | Reuse on stated terms; England-specific; low priority |
| openFDA drug labels | corpus | conditional | CC0 except marked third-party data; US labels; high-risk topic |
| PMC Open Access Subset | corpus | conditional (deferred) | Licence varies per article; store and filter it |
| PubMedQA (pqa_labeled) | evaluation | **approved** | MIT; evaluation only; do not redistribute abstracts |
| MedMCQA | evaluation | conditional | Apache-2.0 declared, but rights in the exam questions are unclear |
| MedQA | evaluation | conditional | Licence not confirmed; read the official repo first |
| MedQuAD | evaluation | conditional | Licence file not read; overlaps with MedlinePlus (leakage) |
| ChatDoctor / HealthCareMagic | corpus | unreviewed | Excluded: scraped consultations, rights unknown, scope conflict |
| Medical Meadow WikiDoc | corpus | unreviewed | Excluded until reviewed |

## Project rules

1. **No source text is committed to the repository.** Content is ingested at run time into the local database. The repo holds the registry and code only.
2. **Every stored document carries** its source id, URL, retrieval date, licence string and corpus version.
3. **Non-commercial content (WHO, some PMC) is flagged** so that a commercial deployment can switch it off.
4. **Evaluation datasets are never training data and never RAG corpus.** The validator enforces this.
5. **Re-check the terms before any public release.** For example, MedlinePlus's own terms page was last updated in 2022.

## Recommended corpus v0: MedlinePlus health topics

- The official page lists health topic summaries and medical test information as public domain, and offers them as daily XML files (Tuesday to Saturday), so no scraping is needed. The XML has title, URL, language, creation date, ID, MeSH terms and the full summary for each topic. The file for 2026-11-03 was about 29 MB.
- Record the XML file date as the corpus version.
- Caveats: the content is US-centric consumer information, not clinical guidelines, so it cannot support claims about dosing or individual treatment.

Later candidates, once their open tasks are done: CDC pages (allowlist), openFDA labels for medication questions (high risk; strict disclaimers), WHO (non-commercial deployments only).

## Notes on evaluation data

- **Leakage risk:** MedQuAD includes questions built from MedlinePlus health topics, which are also in corpus v0. Use it to test whether retrieval finds the right source page, not as independent proof that answers are good.
- **PubMedQA** tests reading research abstracts (yes/no/maybe), not patient communication. Its official test set has 500 questions, so confidence intervals will be wide.
- **MedMCQA and MedQA** are exam benchmarks. Accuracy on them says nothing about patient safety and must not be presented that way. Models may also have seen them during pretraining.
- **None of these datasets covers patient-facing communication, safe uncertainty or referral behaviour.** That evaluation set has to be written and reviewed by us (Phase 3), ideally with clinician input.

## Gaps: not researched

- **India-specific sources** (national health ministry and ICMR material, for example). This matters for the stated public-good audience and is the biggest content gap.
- Other NIH institute sites, StatPearls, Cochrane, NICE and guideline bodies.
- Legal review for any real deployment, including health-data protection law.

## Open tasks before first ingestion

1. CDC: read the full "Use of Agency Materials" requirements and record them.
2. WHO: confirm the licence of the specific website pages (fact sheets) to be used.
3. NHS: read sections 3 onward of the terms for attribution and adaptation rules.
4. MedQA and MedQuAD: read the repository licence files directly.
5. MedlinePlus: re-read the terms page at release time.

## Source pages

- MedlinePlus terms: https://medlineplus.gov/about/using/usingcontent/ and XML files: https://medlineplus.gov/xml.html
- CDC: https://cdc.gov/other/agencymaterials.html
- WHO: https://www.who.int/copyright and https://www.who.int/about/who-we-are/publishing-policies/copyright
- NHS: https://www.nhs.uk/our-policies/terms-and-conditions/ and https://www.nhs.uk/our-policies/terms-and-conditions/content-not-licensed-for-re-use/
- openFDA: https://open.fda.gov/license and https://open.fda.gov/terms
- PMC: https://pmc.ncbi.nlm.nih.gov/tools/openftlist and https://pmc.ncbi.nlm.nih.gov/tools/textmining/
- PubMedQA: https://huggingface.co/datasets/qiaojin/PubMedQA
- MedMCQA: https://huggingface.co/datasets/openlifescienceai/medmcqa
- MedQA: https://github.com/jind11/MedQA
- MedQuAD: https://github.com/abachaa/MedQuAD
