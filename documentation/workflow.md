# GreenUpPCB LIS - Minimum Lifecycle & Workflow Specification

## 1. Core Lifecycle Overview
The laboratory follows a strict 7-stage lifecycle for incoming boards:
`Receive PCB` → `Register` → `Diagnose` → `Repair/Retrofit` → `Test` → `Report` → `Archive/Close`

---

## 2. Detailed Lifecycle Steps

### Step 1: Receive PCB
* **Who Performs It:** Lab Technician
* **Information Entered (Input):** Physical PCB, delivery slip, client identification.
* **Information Read:** Physical board markings, visual condition.
* **Output Produced:** Physical handover confirmation, intake queue status.

### Step 2: Register PCB
* **Who Performs It:** Lab Technician / System Administrator
* **Information Entered (Input):** Internal tracking reference (unique), customer name/contact, equipment type, manufacturer, model, serial number, date received, initial failure description.
* **Information Read:** Existing reference codes in database to prevent duplication.
* **Output Produced:** Created database record with initial status `received`.

### Step 3: Diagnose
* **Who Performs It:** Hardware / Electronics Specialist
* **Information Entered (Input):** Inspection date, failure root causes, diagnostic findings, technical notes.
* **Information Read:** PCB registration details, reported failure description, equipment model specs.
* **Output Produced:** Diagnosis record linked to PCB, status update to `in_diagnosis`.

### Step 4: Repair / Retrofit
* **Who Performs It:** Repair Technician
* **Information Entered (Input):** Repair date, action taken (soldering, trace fix, cleaning), replaced components list, technical notes.
* **Information Read:** Diagnostic findings and identified faulty parts.
* **Output Produced:** Repair log linked to PCB, status update to `repaired`.

### Step 5: Test
* **Who Performs It:** Test Engineer
* **Information Entered (Input):** Test execution date, outcome (`Pass` / `Fail`), functional test measurements, notes.
* **Information Read:** Repair details and test procedures for the specific board.
* **Output Produced:** Test result record, status update to `tested` (or returned to `in_diagnosis` if failed).

### Step 6: Report
* **Who Performs It:** Project Lead / Engineer
* **Information Entered (Input):** Report generation request, optional engineer sign-off notes.
* **Information Read:** Complete PCB history (Customer, Registration, Diagnoses, Repairs, Tests, Images).
* **Output Produced:** Automated PDF Technical Report ready for client delivery and archiving.

### Step 7: Archive / Close
* **Who Performs It:** Lab Supervisor / Admin
* **Information Entered (Input):** Final delivery sign-off, closing remarks.
* **Information Read:** Generated PDF report, quality assurance check, test results.
* **Output Produced:** Lifecycle completed, status update to `closed`.
