# ![SafeDesk](https://github.com/StudiYash/SafeDesk/blob/main/SafeDesk%20Logo.png)

<p align="center">

  <!-- ⭐ GitHub Stars -->
  <a href="https://github.com/StudiYash/SafeDesk/stargazers">
    <img src="https://img.shields.io/github/stars/StudiYash/SafeDesk?style=for-the-badge&logo=github&color=yellow" alt="GitHub Stars">
  </a>

  <!-- 🛡️ Project Status -->
  <a href="#project-timeline">
    <img src="https://img.shields.io/badge/Status-Under%20Development-blue?style=for-the-badge&logo=github" alt="Project Status">
  </a>

  <!-- 🐍 Python -->
  <a href="#planned-tech-stack">
    <img src="https://img.shields.io/badge/Python-Desktop%20Security-green?style=for-the-badge&logo=python" alt="Python">
  </a>

  <!-- 🪟 Windows -->
  <a href="#safedesk-application">
    <img src="https://img.shields.io/badge/Platform-Windows-informational?style=for-the-badge&logo=windows" alt="Windows Platform">
  </a>

  <!-- ▶️ Official YouTube Video -->
  <a href="#project-walkthrough-coming-soon">
    <img src="https://img.shields.io/badge/Watch-Project%20Walkthrough%20Coming%20Soon-red?style=for-the-badge&logo=youtube" alt="Project Walkthrough Coming Soon">
  </a>

</p>

---

## Project Introduction 🛡️

### Abstract

**SafeDesk** is a Windows-focused desktop security application designed to protect an already logged-in laptop session when the owner needs extra security. The system is activated manually by the owner and creates a guarded protection mode where nobody other than the owner should be able to use the laptop.

SafeDesk combines **face recognition**, **password fallback**, **OTP verification**, **panic/recovery access**, **intruder image capture**, **event logging**, **threat-level escalation**, **safe lockdown controls**, and **automatic shutdown escalation** to protect sensitive work from unauthorized physical access.

The core idea is simple:

> When the owner activates SafeDesk, the laptop enters a protected security mode.  
> If the owner returns, they can unlock it easily using face recognition or fallback authentication.  
> If an intruder tries to access the laptop, SafeDesk captures evidence, logs the attempt, and escalates protection based on the severity of the threat.

SafeDesk is not designed to replace the Windows login screen. It is an additional owner-controlled security layer for situations where the laptop is already logged in but needs temporary high-security protection.

---

## Project Timeline

> ⚠️ **SafeDesk is currently under active development.**

- **Project Restart Date**: June 2026
- **Current Version**: SafeDesk v1
- **Current Status**: Fresh restart and active development
- **Development Approach**: Phase-wise implementation using Codex-assisted development
- **Target Platform**: Windows desktop/laptop systems

---

## My Introduction

| Name | GitHub Profile | LinkedIn Profile |
|------|----------------|------------------|
| **Yash Suhas Shukla** | [GitHub](https://github.com/StudiYash) | [LinkedIn](https://www.linkedin.com/in/yash-shukla-2024aiguy/) |

<div align="center">
  <img src="https://github.com/StudiYash/SafeDesk/blob/main/support_files/About%20Me.gif" alt="Introduction GIF" width="800" height="450">
</div>

---

## Run SafeDesk Locally 🚀

SafeDesk will be runnable locally as a Windows desktop security application after the core implementation is completed.

The final local setup guide will include installation, configuration, Gmail app password setup, camera setup, safe test mode, feature validation, and Windows packaging instructions.

<p align="center">
  <a href="#local-setup-guide-coming-soon">
    <img src="https://img.shields.io/badge/View-Local%20Setup%20Guide%20Coming%20Soon-gold?style=for-the-badge&logo=markdown" alt="Local Setup Guide Coming Soon">
  </a>
</p>

### Local Setup Guide Coming Soon

`LOCAL_SETUP_GUIDE.md` will be added after the main application workflow becomes stable.

---

## Methodology ✨

The methodology of **SafeDesk** is built around a controlled, owner-activated security workflow. Instead of running continuously during normal laptop usage, SafeDesk is launched only when the owner wants an extra layer of protection over sensitive work.

<p align="center">
  <a href="#methodology-diagram-coming-soon">
    <img src="https://img.shields.io/badge/View-SafeDesk%20Methodology%20Diagram%20Coming%20Soon-blue?style=for-the-badge&logo=github" alt="SafeDesk Methodology Diagram Coming Soon">
  </a>
</p>

### Methodology Diagram Coming Soon

A complete SafeDesk methodology diagram will be added after the full system workflow is finalized.

### 1. Owner Activation

- The owner manually launches SafeDesk using a desktop shortcut or keyboard shortcut.
- SafeDesk starts a protected session only when the owner intentionally activates it.
- A short activation countdown may be shown before protected mode begins.
- The owner can cancel activation using approved recovery credentials.

### 2. Protected Mode

- SafeDesk opens a fullscreen, topmost security interface.
- The laptop enters a guarded state.
- Access is controlled through SafeDesk authentication workflows.
- Camera monitoring starts for owner verification and intruder detection.
- Safe recovery options remain available to prevent accidental lockout.

### 3. Owner Verification

SafeDesk verifies the owner through layered authentication:

- **Face Recognition Unlock**: The easiest and fastest owner unlock method.
- **Password Fallback**: Used if face recognition fails or times out.
- **OTP Verification**: Adds an email-based verification layer.
- **Panic / Recovery Code**: Emergency access method for safe recovery.

### 4. Intruder Detection

If an unknown person attempts to access the laptop:

- SafeDesk detects the unknown face.
- An intruder image is captured.
- The event is stored locally.
- Threat level is increased.
- Optional alarm and email alert actions may be triggered.

### 5. Threat Escalation

SafeDesk tracks suspicious activity using a threat-level system.

Examples of forceful access attempts include:

- Repeated unknown face detection.
- Multiple wrong password attempts.
- Multiple wrong OTP attempts.
- Attempts to close or bypass the protected screen.
- Continuous unauthorized presence near the laptop.

### 6. Shutdown Escalation

If unauthorized attempts continue, SafeDesk escalates to automatic shutdown.

Before shutdown:

- Final warning is displayed.
- Final intruder image is captured.
- Final event log is written.
- Owner can cancel using approved recovery methods.
- Real shutdown remains disabled in demo/safe test mode.

### Key Advantages of the Methodology

- **Owner-Controlled Security**: SafeDesk activates only when needed.
- **Layered Authentication**: Face, password, OTP, and panic recovery work together.
- **Evidence Capture**: Intruder photos and events are stored locally.
- **Threat Awareness**: Suspicious behavior is classified using escalation levels.
- **Safety First**: Lockdown and shutdown features are designed with recovery paths.
- **Local Privacy**: Sensitive data remains on the owner’s machine by default.

---

## SafeDesk Security Workflow 🔐

The SafeDesk protection flow is designed to be strict against intruders but recoverable for the owner.

```text
Owner activates SafeDesk
        ↓
Activation countdown begins
        ↓
Protected mode starts
        ↓
Camera monitoring begins
        ↓
Owner unlock attempt
        ↓
Face recognized?
   ┌────┴────┐
   │         │
  Yes        No
   │         ↓
Unlock   Password fallback
             ↓
      Password correct?
        ┌────┴────┐
        │         │
       Yes        No
        │         ↓
      OTP     Threat level increases
        ↓
   OTP correct?
   ┌────┴────┐
   │         │
  Yes        No
   │         ↓
Unlock   Threat level increases
             ↓
  Repeated forceful attempts?
             ↓
      Shutdown escalation
```

---

## SafeDesk Application Architecture 🧠

SafeDesk is built as a single Windows desktop application where the interface, security engine, authentication system, logging system, and protection workflows work together inside one master project structure.

<p align="center">
  <a href="#application-architecture-diagram-coming-soon">
    <img src="https://img.shields.io/badge/View-Application%20Architecture%20Diagram%20Coming%20Soon-purple?style=for-the-badge&logo=github" alt="Application Architecture Diagram Coming Soon">
  </a>
</p>

### Application Architecture Diagram Coming Soon

A full SafeDesk application architecture diagram will be added after the implementation is completed.

### High-Level Architecture

```text
SafeDesk Application
│
├── GUI Layer
│   ├── Setup Wizard
│   ├── Protected Mode Screen
│   ├── Authentication Screens
│   ├── Dashboard
│   └── Settings Panel
│
├── Security Engine
│   ├── Activation Controller
│   ├── Threat Level Manager
│   ├── Forceful Access Detector
│   └── Shutdown Escalation Controller
│
├── Vision System
│   ├── Camera Manager
│   ├── Owner Face Registration
│   ├── Face Recognition
│   ├── Basic Liveness Verification
│   └── Intruder Capture
│
├── Authentication System
│   ├── Password Verification
│   ├── OTP Verification
│   ├── Panic / Recovery Code
│   └── Attempt Control
│
├── Storage and Logging
│   ├── Local Configuration
│   ├── Local Secrets Handling
│   ├── SQLite Event Logs
│   ├── Owner Face Data
│   └── Intruder Evidence
│
├── Alert System
│   ├── Email Alerts
│   ├── OTP Emails
│   └── Optional Alarm
│
└── Safety Layer
    ├── Demo / Safe Test Mode
    ├── Lockdown Recovery
    ├── Watchdog Recovery
    └── Safe Shutdown Controls
```

---

## SafeDesk Application Modules ⚙️

SafeDesk keeps the desktop interface and core security logic inside one unified project. Instead of separating the project into frontend and backend repositories, the system is organized into focused internal modules.

### 1. GUI Layer

The GUI layer manages all user-facing screens.

Main responsibilities:

* First-time setup wizard.
* Fullscreen protected mode.
* Owner authentication screens.
* Intruder history dashboard.
* Settings panel.
* Safe recovery prompts.

### 2. Configuration Manager

The configuration manager controls local settings and setup status.

Main responsibilities:

* Load public-safe default configuration.
* Load local private configuration.
* Validate required setup values.
* Prevent unsafe startup when setup is incomplete.
* Keep real credentials outside GitHub.

### 3. Vision System

The vision system handles webcam-based security features.

Main responsibilities:

* Camera initialization.
* Owner face registration.
* Face encoding generation.
* Face recognition.
* Unknown face detection.
* Basic liveness verification.
* Intruder image capture.

### 4. Authentication System

The authentication system verifies the owner through multiple layers.

Main responsibilities:

* Password fallback.
* Hashed password storage.
* OTP generation and verification.
* Panic/recovery code verification.
* Attempt limits and cooldowns.

### 5. Intrusion System

The intrusion system detects and records unauthorized access.

Main responsibilities:

* Unknown face event handling.
* Intruder image saving.
* Suspicious behavior tracking.
* Threat level updates.
* Alert triggers.

### 6. Threat Level Engine

The threat level engine decides how SafeDesk should respond to suspicious activity.

Threat levels:

```text
Level 0: Safe / idle
Level 1: Unknown face detected
Level 2: Repeated unknown face detection
Level 3: Failed password attempts
Level 4: Failed OTP attempts or forced exit attempt
Level 5: Shutdown escalation
```

### 7. Logging System

The logging system records important events locally.

Main responsibilities:

* SQLite event database.
* Authentication attempt logs.
* Intruder event logs.
* Threat level change logs.
* Shutdown escalation logs.
* Error logs.

### 8. Lockdown Controller

The lockdown controller manages protected mode restrictions.

Main responsibilities:

* Fullscreen topmost protection.
* Safe input restriction.
* Admin privilege checks.
* Emergency unblock.
* Crash recovery.
* Watchdog recovery.

### 9. Alert System

The alert system notifies the owner when important security events occur.

Main responsibilities:

* OTP emails.
* Intruder alert emails.
* Shutdown warning emails.
* Optional alarm sound.
* Silent evidence mode support.

### 10. Dashboard and Settings

The dashboard and settings system helps the owner manage SafeDesk.

Main responsibilities:

* View intruder history.
* View logs.
* Export logs.
* Delete local evidence.
* Change security settings.
* Retake owner face samples.
* Test camera, email, face recognition, and shutdown dry-run.

---

## Core Features 🧩

* Owner-activated extra-security mode.
* Desktop shortcut or keyboard shortcut launch.
* First-time setup wizard.
* Owner profile setup.
* Secure local configuration.
* Local secrets management.
* Owner face registration.
* Face encoding generation.
* Fullscreen protected mode.
* Face recognition unlock.
* Basic liveness verification.
* Password fallback.
* OTP fallback.
* Panic/recovery code.
* Intruder face detection.
* Intruder image capture.
* Threat level system.
* Forceful access detection.
* Automatic shutdown escalation.
* Optional alarm.
* Email alerts.
* SQLite event logging.
* Intruder history dashboard.
* Settings panel.
* Safe input lockdown.
* Watchdog recovery.
* Demo/safe test mode.
* PyInstaller packaging.
* Public documentation.
* Clean setup guide.

---

## Security Modes 🛡️

### Standard Mode

Balanced protection for typical extra-security use.

* Face unlock.
* Password fallback.
* OTP fallback.
* Intruder capture.
* Event logging.
* Shutdown only after repeated failures.

### Strict Mode

Stronger verification and faster escalation for higher-risk situations.

* Face unlock preferred.
* Password and OTP required if face fails.
* Unknown face captured immediately.
* Lower attempt limits.
* Faster shutdown escalation.

### Silent Evidence Mode

Quiet evidence capture with minimal visible warning.

* Capture unknown faces quietly.
* Log suspicious events.
* Avoid loud warning initially.
* Escalate only after repeated attempts.

### Demo / Safe Test Mode

Safe testing mode for development and demonstrations.

* No real shutdown.
* No real input blocking.
* No real email sending unless explicitly enabled.
* Logs what would have happened.
* Allows safe validation of security workflows.

---

## Safety and Privacy Model 🧯

SafeDesk is designed around local-first privacy and recovery-first protection.

### Local Data

SafeDesk may store the following data locally:

* Owner face images.
* Owner face encodings.
* Intruder images.
* SQLite event logs.
* Local configuration files.
* Local secret files.

### Privacy Rules

* No owner images should be committed to GitHub.
* No intruder images should be committed to GitHub.
* No `.env` files should be committed to GitHub.
* No local secret files should be committed to GitHub.
* No SQLite logs or databases should be committed to GitHub.
* No cloud sync is enabled by default.
* Sensitive data remains local by default.

### Safety Rules

* Safe recovery must exist before lockdown is enabled.
* Real shutdown must remain disabled in demo/safe test mode.
* Real input blocking must not run without recovery.
* Panic/recovery code must be available.
* Shutdown escalation should include a cancellation window for the owner.
* Watchdog recovery should prevent accidental lockout.

---

## Project Structure 📁

```text
SafeDesk/
│
├── SafeDesk Logo.png
├── README.md
├── LICENSE
├── CLA.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTORS.md
├── CONTRIBUTING.md
├── .env.example
├── config.example.json
├── requirements.txt
├── main.py
│
├── support_files/
│   └── About Me.gif
│
├── src/
│   └── safedesk/
│       ├── app/
│       ├── config/
│       ├── gui/
│       ├── auth/
│       ├── vision/
│       ├── intrusion/
│       ├── lockdown/
│       ├── alerts/
│       ├── logging_system/
│       ├── storage/
│       └── utils/
│
├── assets/
│   ├── images/
│   ├── icons/
│   └── audio/
│
├── data/
│   ├── owner/
│   ├── intruders/
│   ├── logs/
│   ├── cache/
│   └── config/
│
├── docs/
│   ├── blueprints/
│   ├── phases/
│   ├── safety/
│   └── user_guide/
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── scripts/
└── build_tools/
```

### Folder Purpose

| Folder / File         | Purpose                                                         |
| --------------------- | --------------------------------------------------------------- |
| `src/safedesk/`       | Main SafeDesk Python package                                    |
| `assets/`             | Application runtime assets such as images, icons, and audio     |
| `support_files/`      | README and showcase media                                       |
| `data/`               | Local runtime data folders; private contents ignored from Git   |
| `docs/`               | Public documentation, blueprints, safety notes, and user guides |
| `tests/`              | Unit and integration tests                                      |
| `scripts/`            | Helper scripts                                                  |
| `build_tools/`        | Packaging and build support                                     |
| `.env.example`        | Safe example environment file                                   |
| `config.example.json` | Safe example configuration file                                 |

---

## Planned Tech Stack 🛠️

* Python
* Tkinter or CustomTkinter
* OpenCV
* `face_recognition` or alternate face recognition backend
* SQLite
* `python-dotenv`
* SMTP/email
* `bcrypt`, Argon2, or PBKDF2
* `pygame` or alternate alarm library
* PyInstaller
* Windows-specific APIs where required

---

## GitHub Safety Notes 🔒

The repository is configured to protect local and sensitive data.

Ignored by Git:

* `.env` files.
* Local secret files.
* Local configuration files.
* Owner face images.
* Intruder images.
* SQLite databases.
* Runtime logs.
* Virtual environments.
* Build outputs.
* Tool/agent metadata.
* Local phase execution reports.

Only public-safe source code, documentation, examples, and placeholder files should be committed.

---

## Development Roadmap 🧭

| Phase    | Name                                                |
| -------- | --------------------------------------------------- |
| Phase 0  | Project Reset and Repo Hygiene                      |
| Phase 1  | Folder Structure, Foundation Files, and Main README |
| Phase 2  | Blueprint Documentation                             |
| Phase 3  | Configuration and Local Secrets System              |
| Phase 4  | GUI Shell and App Navigation                        |
| Phase 5  | First-Time Setup Wizard                             |
| Phase 6  | Owner Face Registration                             |
| Phase 7  | Face Recognition Unlock                             |
| Phase 8  | Basic Liveness Verification                         |
| Phase 9  | Password and Panic Code Authentication              |
| Phase 10 | OTP Authentication and Email System                 |
| Phase 11 | SQLite Logging System                               |
| Phase 12 | Intruder Detection and Image Capture                |
| Phase 13 | Threat Level and Forceful Access System             |
| Phase 14 | Protected Mode and Safe Lockdown                    |
| Phase 15 | Shutdown Escalation                                 |
| Phase 16 | Dashboard and Intruder History                      |
| Phase 17 | Settings Panel                                      |
| Phase 18 | Alarm System and Alert Enhancements                 |
| Phase 19 | Testing, Safety Review, and Cleanup                 |
| Phase 20 | Packaging and Public Release Preparation            |

---

## SafeDesk Application 💻

SafeDesk will be packaged as a Windows desktop application.

### Planned Windows Application Features

* First-time setup wizard.
* Protected mode launcher.
* Owner face registration.
* Face recognition unlock.
* Password and OTP fallback.
* Intruder evidence capture.
* Intruder history dashboard.
* Settings panel.
* Safe test mode.
* Packaged Windows executable.

<p align="center">

  <!-- 📦 SafeDesk Windows Application -->

  <a href="#safedesk-windows-application-coming-soon">
    <img src="https://img.shields.io/badge/Download-SafeDesk%20Windows%20Application%20Coming%20Soon-gold?style=for-the-badge&logo=windows" alt="SafeDesk Windows Application Coming Soon">
  </a>

</p>

### SafeDesk Windows Application Coming Soon

The packaged `SafeDesk.exe` will be added after the application workflow is completed and tested.

---

## Project Walkthrough Coming Soon 🎬

The official SafeDesk walkthrough video will be created after the project is completed.

<p align="center">
  <a href="#project-walkthrough-coming-soon">
    <img src="https://img.shields.io/badge/Watch-Project%20Walkthrough%20Coming%20Soon-red?style=for-the-badge&logo=youtube" alt="Project Walkthrough Coming Soon">
  </a>
</p>

---

## License 📄

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License**. For more details, please refer to the [LICENSE](https://github.com/StudiYash/SafeDesk/blob/main/LICENSE) file in this repository.

By using this project, you agree to give appropriate credit, not use the material for commercial purposes without permission, and share any adaptations under the same license.

Attribution should be given as:

> **SafeDesk by Yash Shukla**
> https://github.com/StudiYash/SafeDesk

Quick overview regarding the permissions of usage of this project can be found on the [LICENSE DEED: CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)

![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)

---

## Contributions 🎉

Contributions are welcome! Feel free to open an issue or submit a pull request.

* **Contribution Guidelines**: Please read the [SafeDesk Contribution Guide](https://github.com/StudiYash/SafeDesk/blob/main/CONTRIBUTING.md) before contributing.
* **Contributor License Agreement (CLA)**: By submitting a pull request, you confirm that you have read and agree to the terms of the [Contributor License Agreement](https://github.com/StudiYash/SafeDesk/blob/main/CLA.md).
* **Code of Conduct**: This project and everyone participating in it are governed by the [SafeDesk Code of Conduct](https://github.com/StudiYash/SafeDesk/blob/main/CODE_OF_CONDUCT.md).
* **Contributors**: See the list of contributors [here](https://github.com/StudiYash/SafeDesk/blob/main/CONTRIBUTORS.md).

Made with ❤️ by [Yash Shukla](https://www.linkedin.com/in/yash-shukla-2024aiguy/)
