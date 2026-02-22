# Hydraulic Resourcing App - User Manual

Version 1.0  
Last updated: February 22, 2026

## Quick Start

1. Sign in with your assigned application password.
2. In the sidebar `Team` table, set each member and daily hours.
3. In `Team dashboard`, enter jobs with required hours, priority, assignee, and optional due date.
4. In `Staff pages`, set non-working days and unavailable hours.
5. Review `Schedule output` cards and table.
6. Save to cloud.

## App Purpose

The purpose of this app is to give teams and management a shared, accurate view of real delivery capacity so commitments can be made with confidence.

- Helps team members track true availability and understand what delivery windows they can commit to.
- Makes scheduling conflicts and clashing priorities visible early so they can be escalated quickly.
- Supports management in identifying staffing pressure and when additional resourcing may be required.
- Highlights opportunities to rebalance work across the team to protect due dates.
- Acts as a safety guardrail so people are not overloaded while project delivery remains realistic and controlled.

## Main Areas

## Team dashboard

- `All jobs input` is the planning queue.
- `Priority >= 1` means active work.
- `Priority = 0` means on hold backlog.
- Output table shows projected start and finish dates by assignee.

### Output KPIs

- **Offset before first overtime (hrs)**: support capacity from other members before first overdue due date.
- **Offset capacity (hrs)**: support capacity before all overdue due dates.
- **Overtime needed (hrs)**: extra hours required to recover overdue due-dated work.
- **On-time jobs %**: due-dated active jobs projected on time.
- **Delivery health**:
  - Healthy: no overtime required
  - Early warning: overtime exists but still below both offset values
  - Warning: overtime exceeds offset before first overtime
  - Critical: overtime exceeds both offset values

## Staff pages

Use this page for one selected person at a time.

### Calendar controls

- **Mark non-working**: full day removed from project capacity.
- **Mark working**: clears non-working and manual unavailable for selected date.
- **Mark unavailable**: subtracts selected hours from project capacity for selected date.

> Effective unavailable used by scheduling = manual unavailable + calendar snapshot unavailable (capped at daily hours).

## Availability

- Shows next available dates and a month capacity view.
- Mode switch:
  - `Active only`
  - `Active plus on hold backlog`

## Sidebar tools

## Cloud sync

- **Save to cloud**: writes current dataset snapshot.
- **Reload from cloud**: loads snapshot.
- **Refresh outputs**: refreshes editor/session display.

## Calander sync

- **Snapshot member**: target member to receive calendar snapshot hours.
- **Link calander**: redirects user to Microsoft login/consent.
- **Refresh calander snapshot**: imports meeting busy time and updates unavailable hours.

## Microsoft Calendar Setup (Admin)

Required secrets:

```toml
MS_CLIENT_ID = "YOUR_ENTRA_APP_CLIENT_ID"
MS_TENANT_ID = "common"
MS_SCOPES = "offline_access openid profile User.Read Calendars.Read"
MS_REDIRECT_URI = "https://hydraulicresourcingapp.streamlit.app/"
```

Entra App Registration:

1. Add redirect URI exactly matching `MS_REDIRECT_URI`.
2. Account type should allow org + personal accounts if desired.
3. Grant delegated permissions used above.

## Troubleshooting

- **Cloud 404 on app_state**: create `app_state` table and policies in Supabase.
- **Link calander error**: verify `MS_CLIENT_ID` and redirect URI are correct and exact match in Entra.
- **Snapshot fails after sign-in**: re-link and confirm `Calendars.Read` scope.
- **Numbers look stale**: use `Refresh outputs`.

## Export to PDF

Use the styled manual at:

`docs/hydraulic_resourcing_user_manual.html`

Then in browser: `Ctrl/Cmd + P` -> `Save as PDF`.
