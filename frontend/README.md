# Project Shikayat Karo — React Frontend

Modern, responsive civic tech frontend built with **React.js (Vite)**, **Tailwind CSS**, and **Axios**, connecting to the Shikayat Karo backend.

---

## Quickstart

### 1. Configure Environment
Ensure `.env` exists in the `frontend/` directory (created automatically):
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 2. Start the Frontend Development Server
```bash
cd frontend
npm run dev
```
The application will launch at:
`http://localhost:3000` (or `http://localhost:5173`)

### 3. Start the Backend Server (in a separate terminal)
```bash
# In the project root directory:
python run.py
```
Backend runs at: `http://127.0.0.1:8000`

---

## 1-Click Evaluation Personas

For rapid testing and grading, use the top **Demo Bar** or visit `/login` for single-click login with password `password123`:
- **Dr. Arvind Sharma (Chief Admin)**: `admin@demo`
- **Rajesh Kumar (Facility Incharge)**: `handler@demo`
- **Priya Verma (Student Citizen)**: `student@demo`
- **Guest / Public Citizen**: Submit anonymously or track grievances without login

---

## Key Features & Pages
1. **Dashboard & Heatmap (`/`)**: High-level KPI metrics and 2D spatial canvas mapping risk across campus sectors.
2. **File Grievance (`/submit`)**: Multilingual grievance filing (English, Hindi, Hinglish) with instant AI diagnostic breakdown modal and zero-leakage anonymous access codes.
3. **Track Grievance (`/track`)**: Unauthenticated grievance pipeline tracking (`Submitted` → `AI Analysed` → `Assigned` → `In Progress` → `Resolved`).
4. **Incident Clustering Suggestions (`/suggestions`)**: Admin & Handler review of multi-factor AI groupings with one-click escalation to Parent Incidents.
5. **Incidents Management (`/incidents` & `/incidents/:id`)**: Impact score ranked backlog, SLA countdowns, resolution intelligence, department assignment, and status transitions.
6. **Demo Simulator (`/demo`)**: 1-click execution of the 5-complaint multilingual water leak story and SLA virtual time machine.
