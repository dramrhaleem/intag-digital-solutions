# INTAG Proposal v2 - Template Distillation Contract

## Reference

- Absolute path: `C:\Users\amroh\Documents\AI Product Dev Intag\brand\intag\templates\proposal\INTAG_Proposal_Starter_AR_v2.docx`
- SHA-256: `f1c4c1fab0f4d46d3d83c63f8351cc0b87a5337d95155a826f3b5538c73b25d8`
- Size and package-part hashes: `reference-package-inventory.json`
- Page count: 5 pages, rendered through Microsoft Word.
- Section count: 1.
- Render evidence: `..\qa-v2\render-proposal-word\page-1.png` through `page-5.png`.
- Section evidence: `reference-section-audit.txt`.
- Style evidence: `reference-style-evidence.json`.

## Page system

- A4 portrait: 8.27 x 11.69 in.
- One section with no odd/even or first-page header split.
- Margins: left/right 0.88 in, top 0.72 in, bottom 0.68 in.
- Header distance 0.28 in; footer distance 0.30 in.
- Exact content width: 9360 DXA.
- Seven body tables, all with `tblW=9360`, `tblInd=120`, fixed DXA grids, expandable rows, and repeating header rows.
- Manual page breaks create five stable page roles: cover, executive summary, scope/method, timeline/responsibilities, investment/approval.

## Typography and direction

- Reference body face: IBM Plex Sans Arabic. Target English deviation required by the user: Poppins Regular/Bold embedded in the final DOCX.
- Reference is RTL. Target English deviation required by the user: LTR paragraphs, lists, tables, headers, and footer.
- Body: 11 pt, 8 pt after, 1.333 line spacing, justified on proposal pages.
- Title: 30 pt bold, centered; no paragraph border.
- Subtitle: 13 pt, centered, muted slate, not italic in the target.
- Heading 1: 18 pt bold, deep blue, 18 pt before / 10 pt after.
- Heading 2: 14 pt bold, deep blue, 12 pt before / 6 pt after.
- Heading 3: 12.5 pt bold, deep green, 8 pt before / 4 pt after.
- Kicker: 8.5 pt bold deep green; lead: 13 pt bold midnight.
- Table text: 9.25 pt; white bold headers on midnight fill.
- Lists: real Word numbering, with target LTR marker/text indents inherited from the narrative-proposal preset.

## Components

- Cover: centered approved Logo 02, kicker, editable title/subtitle, client line, two-column metadata table, approval-state callout, placeholder note.
- Running header: brand name plus approval-state line.
- Running footer: document label, editable-template label, version, PAGE and NUMPAGES fields.
- Executive summary: context, challenge/outcome, evidence-state table, success criteria, decision request, open questions.
- Scope/method: four-service scope matrix, four numbered delivery stages, boundaries, dependencies/inputs.
- Timeline/responsibilities: four-stage schedule matrix, INTAG/client responsibilities, schedule rule, three review gates.
- Investment/approval: estimate-basis matrix without final prices, commercial assumptions, no-guarantee boundary, two-column approvals.
- Callouts use light mineral or mist fills with one brand-color accent edge.
- Logo image relationship and drawing geometry are preserve-only. Alternative diagonal logo geometry is prohibited.

## Editable slot map

- Header/footer text: translate to English; retain field codes and page furniture.
- Cover title, subtitle, client, date, owner, and status: translate prompts and preserve placeholder brackets.
- Body prose and prompts: translate into natural professional English; preserve the semantic role and approximate capacity of every slot.
- Tables: translate every header, row label, placeholder, status, and approval line; keep row/column counts and DXA grids unchanged.
- Lists: translate every item; keep real numbering definitions and the same number of items.
- Metadata: English title/subject/keywords/comments only; personal creator fields must be scrubbed.
- Image alt/title: English description of approved Logo 02.
- Remove any artificial-intelligence references, tool names, or related metadata. Use `Technology & Digital Products` for the technical service line.

## Package preservation

- Preserve page geometry, section count, image payloads, logo relationship, theme, document settings, table grids, table borders/fills, field-code structure, and content-type plumbing.
- Styles, numbering, font table, font relationships, paragraph direction, table direction, visible text, image alt text, and core metadata may change only as required for English LTR output.
- No comments, tracked changes, custom properties, content controls, footnotes, or external hyperlinks are present or permitted in the final.
- Full package-part baseline is recorded in `reference-package-inventory.json`.

## Fidelity gates

- The retained Arabic reference must remain byte-for-byte unchanged during authoring.
- Final page count must remain 5 and page geometry must remain A4 with 9360 DXA content width.
- Every page must remain recognizably source-derived and use the same content density and recurring chrome.
- Logo 02 must retain exact orthogonal SVG geometry: `M20 84V28H72` and `M108 44V100H56`.
- Poppins Regular/Bold must be embedded; every visible text run must resolve to Poppins.
- All visible text and metadata must be English, except the immutable logo artwork.
- Render every page through Microsoft Word and inspect at 100% for clipping, overlap, broken tables, wrapping drift, or unexplained movement.
- Accessibility, table geometry, OOXML integrity, metadata privacy, and prohibited-term audits must pass before delivery.
