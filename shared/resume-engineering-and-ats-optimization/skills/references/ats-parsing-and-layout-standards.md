# ATS Parsing Mechanics & Layout Engineering Standards

## 1. How Modern ATS Parsers Process Resumes
ATS platforms vary by vendor and configuration. Many extract resume text and attempt to identify contact details, roles, dates, skills and education; this document describes general risk-reduction practices, not verified behavior of a specific vendor.

```
[Raw PDF / DOCX] 
      │ (Text extraction; OCR only when needed)
      ▼
[Linear Text Stream] 
      │ (Regex & NLP Chunking)
      ▼
[Section Classification: Summary, Skills, Experience, Education]
      │ (Entity Extraction: Dates, Job Titles, Companies, Keywords)
      ▼
[Parsed Candidate Profile (Candidate DB)]
```

### Parser Vulnerability Modes
- **Multi-Column & Sidebars**: Parsers read horizontally across columns (e.g. reading line 1 of column 1 directly followed by line 1 of column 2), causing broken sentence fragments and corrupted chronological dates.
- **Tables & Floating Text Boxes**: Most enterprise parsers ignore text contained inside Word/PDF drawing canvases, text boxes, and nested table cells.
- **Non-Standard Section Headings**: Using creative headings like "Where I've Been" or "Technologies in My Arsenal" causes the parser to lump experience into general notes or miss skills entirely.
- **Header & Footer Storage**: Information placed in word processor headers or footers is frequently skipped by OCR/text extractors. Contact info must reside in the body.
- **Complex Graphic Characters**: Custom bullet icons, font symbols, and emoji can parse as garbled characters (e.g. `\uFFFD` or `?`), corrupting keyword matching.

---

## 2. Mandatory Structural Standards

| Element | Recommended Standard | High-Risk Anti-Pattern |
| :--- | :--- | :--- |
| **Layout** | Single-column linear vertical hierarchy | 2-column resume with left sidebar |
| **Section Headings** | Standard titles: `Professional Summary`, `Technical Skills`, `Professional Experience`, `Key Projects`, `Education` | Creative titles: `My Story`, `Tech Stack Arsenal`, `Career Journey` |
| **Date Format** | `MM/YYYY – MM/YYYY` or `MMM YYYY – Present` (e.g. `03/2021 – Present`) | Ambiguous year-only (`2021–2024`) or non-delimited text |
| **Bullets** | Standard Unicode hyphen (`-`) or round bullet (`•`) | Custom SVG arrows, Wingdings, star icons |
| **File Formats** | Standard text-based PDF or clean DOCX | Rasterized image-only PDF or Canva export with layered canvases |

---

## 3. Semantic Keyword Optimization vs. Keyword Stuffing

### Safe Keyword Density
- Keywords must appear naturally inside context-rich experience bullets with associated tooling and business problems.
- Example: "Built scalable REST services in **NestJS** with **TypeScript** and **MySQL**."

### The "White Font / Invisible Text" Penalty
- Hidden text and keyword stuffing are misleading and may produce unreliable extraction or undermine recruiter trust; do not use them. Do not assert automatic rejection without vendor-specific evidence.

### Acronym & Full Form Pairing
- In technical domains, pair both the standard acronym and full term on first mention where relevant:
  - `ATS (Applicant Tracking System)`
  - `REST (Representational State Transfer)`
  - `API (Application Programming Interface)`

---

## 4. Typography, Margins & Padding Engineering Standards

### A. Page Margins (0.5 in – 0.75 in)
- **Golden Rule**: Maintain between **0.5 inch (12.7 mm / 720 twips)** and **0.75 inch (19 mm / 1080 twips)** on all four sides.
- **The Micro-Margin Danger (< 0.5 in)**: Setting margins to 0.2" or 0.3" causes text near the edges to be cropped when scanned or rendered into standard ATS OCR engines.
- **The Macro-Margin Waste (> 1.0 in)**: 1-inch margins unnecessarily squeeze content, pushing an otherwise clean 1-page resume onto a second page.

### B. Font Hierarchy & Sizing
- **Candidate Name**: **18pt – 22pt** (Bold). Dominant anchor at page top.
- **Section Headings**: **12pt – 14pt** (Bold / Small-Caps). Visual delimiters separating logical blocks.
- **Role Titles & Companies**: **11pt – 12pt** (Bold / Semi-Bold). Distinct from body text.
- **Body Text & Bullets**: **10pt – 11pt** (Regular weight; strict floor is **9.5pt**).
- **Small-font readability risk (< 9.5pt)**: Very small body text is harder to read and can degrade OCR on scanned documents; the effect depends on rendering quality.
- **Safe ATS Fonts**: System-standard fonts with 100% vector font embedding: **Calibri, Arial, Helvetica, Georgia, Inter**. Avoid non-standard Google webfonts without embedded fallbacks.

### C. Spacing, Line Height & Padding
- **Line Spacing (Line Height)**: **1.1x to 1.15x** (or single spacing with 2pt–3pt space-after bullets). Avoid default Word 1.15 + 8pt after, which creates ballooning whitespace.
- **Bullet Padding**: Add **2pt – 3pt** after each bullet to prevent "wall of text" density while preserving scan speed.
- **Section Padding**: Add **6pt – 8pt** space before every Section Heading to create distinct optical grouping.

### D. The Header & Footer Placement Trap
- **Zero Critical Data in Headers**: Never place candidate name, phone number, email address, or LinkedIn URLs in Word or Google Docs Headers or Footers (`<w:header>`, `<w:footer>`).
- Some resume extraction pipelines may miss content stored in Word headers and footers. Put contact details in the main document body as a precaution; no universal rejection percentage is established.
