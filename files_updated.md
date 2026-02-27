When SSO_ENABLED=True:

Existing Azure AD SSO flow works exactly as before (zero changes to SSO code)
6 files modified:

.env — added SSO_ENABLED=False
auth.py — /api/auth/config endpoint
authService.ts — config fetcher
AuthContext.tsx — auto-guest-auth + full bypass
LandingPage.tsx — conditional login header
ProtectedRoute.tsx — skip auth guards

For the work just completed on the RBI and SEBI User Guides, here is the file summary:

File Summary
[NEW] Added
[
RBIUserGuide.tsx
](file:///d:/Adani_Project/aegis_phase_2_dev/Frontend/src/pages/RBIUserGuide.tsx) — Comprehensive guide for the RBI module with custom branding.
[
SEBIUserGuide.tsx
](file:///d:/Adani_Project/aegis_phase_2_dev/Frontend/src/pages/SEBIUserGuide.tsx) — Comprehensive guide for the SEBI module with custom branding.
[MODIFY] Updated
[
RBIAnalysisDashboardLayout.tsx
](file:///d:/Adani_Project/aegis_phase_2_dev/Frontend/src/components/layout/RBIAnalysisDashboardLayout.tsx) — Added sidebar navigation link to the RBI User Guide.
[
SEBIAnalysisDashboardLayout.tsx
](file:///d:/Adani_Project/aegis_phase_2_dev/Frontend/src/components/layout/SEBIAnalysisDashboardLayout.tsx) — Added sidebar navigation link to the SEBI User Guide.
[
App.tsx
](file:///d:/Adani_Project/aegis_phase_2_dev/Frontend/src/App.tsx) — Registered new protected routes for the RBI and SEBI guides.

For the work just completed on the Insider Trading User Guide (Refined), here is the file summary:

File Summary
[NEW] Added
[
InsiderTradingUserGuide.tsx
](file:///d:/Adani_Project/aegis_phase_2_dev/Frontend/src/pages/InsiderTradingUserGuide.tsx) — High-fidelity guide centered on InstaMUFG Portal, NSDL/CDSL/PHY files, and weekly comparison logic. (SEBI content removed).
[MODIFY] Updated
[
InsiderTrading.tsx
](file:///d:/Adani_Project/aegis_phase_2_dev/Frontend/src/pages/InsiderTrading.tsx) — Updated with refined User Guide rendering and navigation.
[
App.tsx
](file:///d:/Adani_Project/aegis_phase_2_dev/Frontend/src/App.tsx) — Registered route for the refined Insider Trading User Guide.