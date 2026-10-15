# Client records and visa document workflow

Reviewed and saved locally on **14 October 2026**. The linked Home Affairs and ACS pages did not display a reliable publication date in the material reviewed, so `published_at` is **unknown** unless the particular page or PDF supplies one. Reopen each source when preparing a real application and record the new access time, source text hash, and any displayed publication or effective date.

## What the local tool stores

`client` stores the given names, family name, other names, name evidence basis, and a correction version in the private SQLite database. Enter names as shown on the relevant identity document and compare them with the actual ImmiAccount form before use. A `passport_seen` label records the local operator's assertion; the program does not authenticate a passport. Avoid recording passport numbers in file names or event logs.

`requirements` imports a **route-specific** list from saved official-page text, with the exact URL, access time, optional publication time, SHA256, quoted requirement, operator preparation note, and any alternative backed by a quotation from a saved official source. The list is always marked incomplete until the actual application and ImmiAccount checklist have been checked. `document` preserves a local copy of a file and suggests a descriptive filename using the stored name and document type. The suggested filename is **not** an official ImmiAccount naming rule. `checklist` shows missing or locally collected items, stale sources, old-name/list versions, saved file paths, and the source dates. `record_upload` can store an operator-reported upload time and evidence note, but performs no upload or independent verification.

The database and files for this workspace live under the selected `.profile/CLIENT/` private root with 0700 directories and 0600 files. They are **not encrypted**. Restrict device and backup access before storing real client data. See [profile workflow](./PROFILE_WORKFLOW.md).

The CLI accepts JSON matching [schemas/client-documents.json](./schemas/client-documents.json). A minimal synthetic sequence is:

```json
{"given_names":"Asha","family_name":"Example","other_names":[],"name_basis":"candidate_reported","provenance":"client supplied name; passport not yet checked","expected_client_version":0}
```

```json
{"route":"500:student","expected_list_version":0,"coverage_note":"Only the named public page reviewed; ImmiAccount checklist outstanding","sources":[{"id":"student_page","url":"https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-listing/student-500","title":"Synthetic example only","accessed_at":"2026-10-14T00:00:00+00:00","published_at":null,"content":"Example requirement text"}],"items":[{"id":"example_record","title":"Example record","source_id":"student_page","source_excerpt":"Example requirement text","necessity":"unknown","preparation_note":"Operator note; verify with the current page","alternatives":[]}]}
```

The example requirement text is **not** a visa rule. Replace it with a current official passage when recording a real case. An empty `items` array can preserve a source observation while making no document claim. Use `{"route":"500:student","requirement_id":"example_record","path":"/private/local/file.pdf"}` for `document` and `{"route":"500:student"}` for `checklist`. After a human uploads, `record_upload` accepts `{"route":"500:student","document_id":"ID_FROM_DOCUMENT_ACTION","uploaded_at":"2026-10-14T00:00:00+00:00","evidence_note":"What the operator observed in ImmiAccount"}`. This is a record of the operator's assertion, not an automated upload receipt.

## Source order for every subclass and stream

1. Read the current subclass **and stream** page, including its “Gather your documents” and “Step by step” sections. Record applicant conditions that change the list.
2. Check the exact application in ImmiAccount. [Home Affairs says the application form tells applicants which documents to attach and when](https://immi.homeaffairs.gov.au/help-support/applying-online-or-on-paper/online/attach-documents-to-your-application). The [student document checklist tool](https://immi.homeaffairs.gov.au/visas/web-evidentiary-tool) is indicative; Home Affairs says the submitted application supplies its own list and may request more evidence. [Student tool disclaimer](https://immi.homeaffairs.gov.au/supporting/Pages/Student/disclaimer-document-checklist-tool.aspx).
3. Where another authority is involved, use that authority's current checklist as a **separate destination**. For example, ACS employment-reference and payment-evidence rules are [published by ACS](https://www.acs.org.au/msa/infohub/employment-references.html) and [its payment-evidence page](https://www.acs.org.au/msa/infohub/payment-evidence.html); an ACS submission checklist is not automatically an ImmiAccount checklist.
4. Record `published_at` only when the source actually gives it. Always record `accessed_at` and the local `saved_at`. A recent save of older material does not update its legal effective date. If an official page is inaccessible or its rule is ambiguous, mark the item unknown and ask for review.

## Preparing or obtaining a document

| Kind | Useful next action | Alternative boundary |
| --- | --- | --- |
| Identity or name-change record | Obtain the genuine record from the issuing authority; keep a clear, complete copy and relevant translation. | Do not generate or edit an identity document. Ask the authority about replacement records. Home Affairs gives [name-change examples](https://immi.homeaffairs.gov.au/check-twice-submit-once/applying-for-a-family-visa/important-information-for-your-application). |
| Employment reference for ACS | Request a truthful letter from an authorised employer signatory using the [current ACS detail list](https://www.acs.org.au/msa/infohub/employment-references.html). A local draft may help the employer, but the employer must verify and issue it. | ACS describes a statutory declaration or affidavit route if a reference cannot be obtained or the person is self-employed; check its linked current conditions before proposing it for a specific episode. Do not treat contracts or position descriptions as interchangeable with the ACS reference. |
| ACS payment evidence | Gather genuine records for the relevant periods from employer and independent sources. | Compare permitted evidence types on the [current ACS payment page](https://www.acs.org.au/msa/infohub/payment-evidence.html); never fabricate payslips, bank records, or tax data. |
| English, qualifications, health, or police evidence | Use the testing body, institution, medical process, or issuing authority specified for the current route. | Record a route-specific exemption or substitute only when the current official rule explicitly supports it. |
| Personal explanation or chronology | Draft locally from the client's verified facts, label missing details, and have the client review the final wording. | A drafted statement cannot replace an official record unless the relevant authority accepts that form of evidence. |

For ImmiAccount, [Home Affairs's general attachment page](https://immi.homeaffairs.gov.au/help-support/applying-online-or-on-paper/online/attach-documents-to-your-application) described accepted formats, a 5 MB limit for most non-photo attachments, non-acceptance of encrypted PDFs, document-category selection, and retaining your own copies when checked on 14 October 2026. These are **saved observations**, not permanent rules; recheck the live page and application-specific screen before upload. The local tool only checks extension and byte size. It does not establish file readability, image clarity, correct category, translation sufficiency, or upload success.

## No universal checklist or document generator

The same framework can track any subclass/stream, but a universal “all visa documents” list would misstate requirements. A passport, employer reference, test result, and applicant statement have different creators and proof standards. The tool can suggest how to obtain an item and can draft an honest applicant-authored statement in a future reviewed workflow; it cannot create authentic third-party or government-issued evidence. No automated upload, payment, or application submission is included.
