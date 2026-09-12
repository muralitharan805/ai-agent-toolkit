# Operational Discovery Frameworks & Field Interviewing Protocols

## Overview

High-conviction software opportunities are discovered by observing operators in their natural working environments, not by soliciting feature wishlists. When people describe their problems in interviews, they frequently request local optimizations to visible symptoms while concealing root operational bottlenecks.

This guide outlines structured discovery frameworks (TRACE, FOCUS, 5-Phase Forensic Engine) and field interview protocols (The Mom Test, operator shadowing) applicable to **any problem discovery domain**.

---

## 1. Unified Discovery Frameworks

### The TRACE Framework
TRACE is an agile, 5-stage operational methodology optimized for rapid process tracing:

```text
┌────────────────────────────────────────────────────────┐
│                  THE TRACE FRAMEWORK                   │
├───────┬──────────────────────┬─────────────────────────┤
│ **T** │ **Trace Workflow**   │ Observe what operators  │
│       │                      │ actually do step-by-step│
├───────┼──────────────────────┼─────────────────────────┤
│ **R** │ **Record Friction**  │ Document delays, errors,│
│       │                      │ workarounds, re-entry   │
├───────┼──────────────────────┼─────────────────────────┤
│ **A** │ **Analyze Causes**   │ Separate symptoms from  │
│       │                      │ structural root causes  │
├───────┼──────────────────────┼─────────────────────────┤
│ **C** │ **Confirm Value**    │ Validate frequency, cost│
│       │                      │ and willingness to pay  │
├───────┼──────────────────────┼─────────────────────────┤
│ **E** │ **Evaluate Solution**│ Only now assess tool    │
│       │                      │ feasibility & wedge fit │
└───────┴──────────────────────┴─────────────────────────┘
```

### The FOCUS Immersion Framework
FOCUS provides a thorough immersion loop when investigating specialized verticals:
1. **Field Immersion**: Sit alongside operators or join technical communities where the friction occurs.
2. **Observation**: Record exact tool transitions, keyboard shortcuts, and manual copy-paste handoffs.
3. **Cause Digging**: Ask "Why did this mismatch happen?" repeatedly until reaching systemic boundaries.
4. **Understanding Economics**: Calculate hourly labor wasted and statutory non-compliance exposure.
5. **Scoring**: Evaluate against the 35-Point Evidence Matrix before writing specifications.

### The 5-Phase Forensic Engineering Pipeline
$$\textbf{Observe} \longrightarrow \textbf{Deconstruct} \longrightarrow \textbf{Probe} \longrightarrow \textbf{Quantify} \longrightarrow \textbf{Stress-Test}$$
- **Observe**: Screen recordings, unversioned spreadsheets, error logs.
- **Deconstruct**: Map each action into the 14 operational workflow nodes.
- **Probe**: Inquire about edge cases, volume spikes, and recent breakdowns.
- **Quantify**: Tally hours wasted, rework frequency, and financial consequences.
- **Stress-Test**: Check existing commercial competitors (< $50/mo) and platform lock-in risks.

---

## 2. Field Interviewing: The Mom Test Protocol

> **The Cardinal Axiom**: Never ask customers what they think of an idea. Ask them what they did the last time they faced the problem.

People are naturally polite and encouraging. If you ask *"Would you pay for an app that automates X?"*, 80%+ of respondents will answer positively—yet zero will purchase upon release. Verbal praise is not validation. Only historical behavior, spent budget, and maintained workarounds indicate demand.

```text
┌────────────────────────────────────────────────────────┐
│               THE MOM TEST CONVERGENCE                 │
├──────────────────────────┬─────────────────────────────┤
│ ❌ Future Hypotheticals  │ "Would you pay $50/month for│
│    (Worthless data)      │ a tool that syncs inventory?│
├──────────────────────────┼─────────────────────────────┤
│ ✅ Past Factual Behavior │ "How many hours did you     │
│    (High-fidelity truth) │ spend reconciling stock last│
│                          │ Tuesday? What broke?"       │
└──────────────────────────┴─────────────────────────────┘
```

### Good Questions vs Bad Questions Cheat Sheet

| ❌ Bad Question (Hypothetical / Bias) | ✅ Good Question (Behavioral / Grounded) | Why It Matters |
|---|---|---|
| *"Do you think our proposed tool is a good concept?"* | *"What do you actually do today when this data is missing?"* | Hypotheticals solicit polite opinions; actual habits reveal true urgency. |
| *"How much would you pay for this software?"* | *"What tools, contractors, or scripts are you currently paying for to manage this?"* | Uncovers active budgets vs wishful thinking. |
| *"Would you like an AI dashboard that alerts you to errors?"* | *"How did you discover the last error that slipped into production or billing?"* | Identifies actual detection mechanisms rather than fantasy features. |
| *"What features should we build into this app?"* | *"Can you show me the file or spreadsheet where this work was done this morning?"* | Exposes real operational artifacts rather than speculative feature lists. |

---

## 3. The Golden Diagnostic Question

When an operator complains about an operational headache, the single most revealing question is:

> **"What do you actually do today when that happens?"**

Their response immediately categorizes the opportunity:
1. *"We don't do anything; we just live with it."* $\longrightarrow$ **REJECT**. Low pain; no budget will be allocated.
2. *"We looked for a tool once, couldn't find one, so we gave up."* $\longrightarrow$ **REJECT**. Inaction indicates low consequence.
3. *"We hired an intern / paid a freelancer / built a 15-tab macro spreadsheet that runs every morning."* $\longrightarrow$ **VALIDATED OPPORTUNITY**. Real human capital and budget are already actively burning.

---

## 4. Operator Shadowing Protocol

To observe authentic operational behavior without prompting:
1. **Pre-Session Setup**: Request to observe an ordinary work shift (e.g., end-of-month reconciliation, weekly release, inventory update). Emphasize: *"I am not evaluating your personal performance; I am studying how different software systems communicate."*
2. **Silent Observation**: Watch the screen without interrupting. Note every time the operator:
   - Switches between browser tabs or windows.
   - Copies text from one tool and pastes it into another.
   - Types numbers from a PDF document into a form.
   - Opens a local spreadsheet to look up reference codes.
3. **Targeted Debrief**: At natural pauses, ask:
   - *"What was the reason for checking that third tab just now?"*
   - *"Where did that CSV file originate, and who created it?"*
   - *"What would occur downstream if this entry was delayed by 24 hours?"*
4. **Hunting Shadow Systems**: Ask to see the desktop folder, bookmarks bar, or shared drive where team members keep their personal reference files. The existence of files named `FINAL_v4_MASTER_DO_NOT_DELETE.xlsx` confirms human glue-work.
