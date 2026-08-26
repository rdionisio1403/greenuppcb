# GreenUpPCB LIS - Requirements, Screen List & User Stories

## 1. MVP Screen List
1. **PCB List Screen:** High-level dashboard/table listing all registered boards with real-time status badges, search, and filtering.
2. **New PCB Screen:** Clean intake form to register a new PCB into the laboratory system.
3. **PCB Detail Screen:** Central single-page view containing complete lifecycle history (timeline, board specs, logs, images, reports).
4. **Add Diagnosis Modal/Form:** Form to record inspection findings, fault descriptions, and technician notes.
5. **Add Repair Modal/Form:** Form to document specific repair actions, procedures, and replaced components.
6. **Add Test Modal/Form:** Form to register electrical/functional test runs and outcomes (`Pass` / `Fail`).
7. **Images Section / Gallery:** Image management area to upload, categorize, and preview high-resolution before/after board photos.
8. **Report Section:** Single-click action to view, generate, and download the standardized PDF technical report.

---

## 2. Prioritized User Stories

### Essential (MVP Scope)
* **US01 [MVP]:** As a technician, I want to register a new PCB with a unique internal reference so that every incoming board can be tracked throughout its lifecycle.
* **US02 [MVP]:** As a technician, I want to view a list of all PCBs with their status badges so that I can immediately identify pending work.
* **US03 [MVP]:** As a user, I want to search and filter PCBs by reference, model, customer, or serial number to locate specific board records quickly.
* **US04 [MVP]:** As a hardware specialist, I want to record diagnosis findings for a PCB to document observed physical and electrical failures.
* **US05 [MVP]:** As a repair technician, I want to log repair operations and list replaced components to maintain a clear audit trail of hardware modifications.
* **US06 [MVP]:** As a test engineer, I want to record functional test results (`Pass` / `Fail`) with notes to verify that the board is operational before delivery.
* **US07 [MVP]:** As a technician, I want to upload high-resolution photos of PCBs (e.g., damaged component vs. repaired joint) to maintain visual documentation.
* **US08 [MVP]:** As a project engineer, I want to generate a clean, one-page PDF technical report containing the entire board history to provide to the client.
* **US09 [MVP]:** As a lab member, I want to view a unified timeline on the PCB Detail screen so that I can see the sequential lifecycle history at a glance.
* **US10 [MVP]:** As an administrator, I want the system to enforce unique internal reference codes so that duplicate registrations are prevented.

### Future Enhancements (Post-MVP / Backlog)
* **US11 [Post-MVP]:** As a laboratory supervisor, I want a metrics dashboard showing monthly throughput and repair success rates.
* **US12 [Post-MVP]:** As a system administrator, I want role-based authentication (JWT) to restrict sensitive configuration and editing actions.
* **US13 [Post-MVP]:** As a user, I want to export customer repair summaries to Excel for inventory and billing coordination.
* **US14 [Post-MVP]:** As a technician, I want to print barcode/QR code labels for physical PCB tagging upon registration.
