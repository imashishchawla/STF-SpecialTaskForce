# Source catalog and freshness rules

Reviewed 14 October 2026. This catalog supplements the [shared operating contract](./operating_contract.md). It does not extend the offline runtime's official-host registry or authorize fetching, uploading candidate facts, or treating third-party data as a visa rule.

## Authority order

1. For current visa requirements, stream opening, occupation lists, points, fees, and processing times, use the relevant current Home Affairs, assessing-authority, or state/territory page. Record the exact stream, URL, access date, applicable cohort, and supporting passage. For current processing times, start with [Home Affairs processing times](https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-processing-times).
2. For a company's current willingness to sponsor, check the specific live vacancy or employer careers page and obtain direct employer confirmation. Historical sponsorship does not prove current accreditation, an open job, or sponsorship for this candidate.
3. Use the sources below only for leads, historical comparisons, or design review. Compare their observation date and underlying data date with the current primary source. If either date is missing or the current source differs, mark the third-party claim unverified. Never promote a newer GitHub commit to proof that its underlying visa data is newer.

For document work, start with the current [Home Affairs ImmiAccount attachment guidance](https://immi.homeaffairs.gov.au/help-support/applying-online-or-on-paper/online/attach-documents-to-your-application), the exact visa stream's “Gather your documents” section, and the actual application's checklist. For student cases, the [document checklist tool](https://immi.homeaffairs.gov.au/visas/web-evidentiary-tool) is indicative, as its [disclaimer](https://immi.homeaffairs.gov.au/supporting/Pages/Student/disclaimer-document-checklist-tool.aspx) explains. If ACS assessment is relevant, separately check its [employment reference](https://www.acs.org.au/msa/infohub/employment-references.html) and [payment evidence](https://www.acs.org.au/msa/infohub/payment-evidence.html) pages. See [document workflow](../DOCUMENT_WORKFLOW.md) for publication, access, and local save dates.

## Supplementary discovery sources

| Source | Limited use | Freshness and verification rule |
| --- | --- | --- |
| [Australian tech employer sponsorship leads](https://github.com/geshan/au-companies-providing-work-visa-sponsorship) | Find companies and career-page links for a job search. | Repository last pushed 21 Nov 2025 when reviewed. Its README includes 2024 and 2025 historical lists and disclaims current sponsorship. Reopen the employer's own careers page and confirm the actual role and sponsorship directly. Do not call this an accredited-sponsor register. |
| [Visa processing-time history](https://github.com/ChangkeunJ/visa-times) | Explore historical changes in published Home Affairs processing-time figures. | Repository last pushed 14 Oct 2026 when reviewed, but a stored reading has its own `Updated` and `EndDate` fields. Compare subclass **and stream**, those dates, and the current [Home Affairs processing-time page](https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-processing-times). Do not predict a person's decision date from percentiles or a historical reading. |

## Reviewed but not added as factual sources

| Link | Decision |
| --- | --- |
| [2025 sponsor-list Right to Know request](https://www.righttoknow.org.au/request/list_of_all_accredited_australia) | The Department closed the request on 16 Apr 2025 after no response/payment; this page provides no released 2025 sponsor list. Do not cite it as evidence of sponsor status. |
| [Right to Know public-authority directory](https://www.righttoknow.org.au/body/list/all) | Directory of public authorities, not migration rules or a sponsor list. Useful only to locate an agency for an information request. |
| [Citizenship processing-time tracker](https://github.com/grainne-b/visa-processing-times) | Tracks citizenship, not visa application processing. Out of scope for the current CV/visa workflow; reconsider only if citizenship research is explicitly added. Its displayed data was for Aug 2026 when reviewed. |
| [Study/post-study community directory](https://github.com/jibranpcccc/study-in-australia-post-study-work-visas-hub) | Repository was pushed 13 Oct 2026, but sampled directory entries included US nursing, aviation, and bar-exam communities. A recent push does not establish Australian migration relevance or validation. Do not use it for route rules or recommendations. |
| [VisaMate](https://github.com/Aiswaryasudhir/visamate) | Architecture example for profile questions, hybrid retrieval, citations, and a visible editable profile. Not a legal source. Its documented Groq/OpenAI hosted processing conflicts with this package's strict local candidate-data policy; do not adopt its provider flow. |
| [AustraliaVisaSkills](https://github.com/ScriptSavvy/AustraliaVisaSkills) | Reference for role-specific checklists and source-refresh prompts, not current law. The README says it has not had comprehensive current-law or legal review. Content is CC BY-NC 4.0; do not copy or install its skills into this package without a separate license and content review. |

## Update procedure

For any cited secondary item, store `source_url`, `observed_at`, `underlying_data_date`, `subclass`, `stream`, `purpose`, and `primary_check_url`. Mark `underlying_data_date=unknown` when unavailable. A fresh observation of an old data set remains historical. If a source is unreachable, preserve the failure and answer with the primary-source gap; do not fill it from memory.
