# Alternative Assessment & Workflow Fit Audit

## Overview
Establishes the criteria for evaluating existing commercial software, native features, spreadsheets, and manual services without jumping to false conclusions.

---

## 1. The Workflow Fit Standard

The simple existence of competitors or incumbent software does NOT mean the workflow is adequately solved.

$$\text{Workflow Fit} = f(\text{Operator Constraints}, \text{Workflow Coverage}, \text{Adoption Friction})$$

### Diagnostic Questions:
1. **Scope Coverage**: Does the alternative handle the exact failure point (e.g. returns reconciliation) or only standard operations (initial dispatch)?
2. **Operator Affordability & Barrier**: Does it demand $500/month or enterprise IT integration when the operator is a $50k SMB?
3. **Regional & Compliance Constraints**: Does it support local regulatory formats (GST, e-invoicing, regional courier APIs)?
4. **Device & Connectivity Constraints**: Does it require desktop Chrome when the frontline worker uses a basic mobile phone in the field?

---

## 2. Non-Software Sufficiency Check
Before assuming software is justified, audit whether non-software solutions are sufficient:
- A printed laminated checklist.
- A standardized Excel/Sheets template.
- A weekly 15-minute sync meeting.
- A WhatsApp business notification group.

If a non-software alternative completely resolves the friction with negligible operational cost, flag `non_software_sufficient: true` and trigger stop checks.
