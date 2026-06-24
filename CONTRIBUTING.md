# Contributing to SafeDesk

First off, thank you for considering contributing to **SafeDesk**!

SafeDesk is a Windows-focused desktop security project that deals with sensitive concepts such as authentication, local secrets, webcam-based owner verification, intruder image capture, local logging, lockdown behavior, and shutdown escalation. Because of this, contributions must be handled carefully, safely, and responsibly.

Following these guidelines helps keep the project useful, secure, and respectful of user privacy.

---

## Code of Conduct

This project and everyone participating in it are governed by the [SafeDesk Code of Conduct](https://github.com/StudiYash/SafeDesk/blob/main/CODE_OF_CONDUCT.md).

By participating, you are expected to uphold this code.

Please report unacceptable behavior to [studiyash@gmail.com](mailto:studiyash@gmail.com).

---

## Contributor License Agreement (CLA)

Before we can accept your contributions, you need to agree to the SafeDesk Contributor License Agreement.

You can read it here:

[SafeDesk Contributor License Agreement](https://github.com/StudiYash/SafeDesk/blob/main/CLA.md)

By submitting a contribution, you agree that your contribution is licensed under the same license as the SafeDesk project:

**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License**

---

## How Can I Contribute?

### 1. Reporting Bugs

If you find a bug, please open an issue on GitHub.

Include as much detail as possible:

- Clear description of the problem.
- Steps to reproduce the issue.
- Expected behavior.
- Actual behavior.
- Screenshots if helpful.
- Error messages or logs if available.
- Operating system details.
- Python version.
- Whether demo/safe test mode was enabled.
- Whether real lockdown, real shutdown, or real email was enabled.

Do not upload private files such as:

- `.env`
- `config.local.json`
- `secrets.local.json`
- Owner face images.
- Intruder images.
- SQLite databases.
- Runtime logs containing sensitive information.

---

### 2. Suggesting Enhancements

Enhancement ideas are welcome.

Good enhancement suggestions should explain:

- What feature you want.
- Why it is useful.
- How it improves SafeDesk.
- Whether it affects security, privacy, lockdown, shutdown, or authentication.
- Whether it should be enabled by default or only in safe/advanced mode.

---

### 3. Improving Documentation

Documentation contributions are welcome.

Useful documentation improvements include:

- Setup instructions.
- Windows troubleshooting.
- Safe test mode guidance.
- Camera setup help.
- Gmail app password setup help.
- Security mode explanations.
- User guide improvements.
- Developer architecture notes.

---

### 4. Submitting Code Changes

To submit code changes:

1. Fork the repository.
2. Create a new branch with a clear name.
3. Make your changes.
4. Test your changes locally.
5. Ensure no private files are included.
6. Submit a pull request with a clear explanation.

Recommended branch name examples:

```text
feature/setup-wizard
feature/threat-level-manager
feature/intruder-dashboard
feature/safe-test-mode
fix/config-validation
fix/email-error-handling
docs/update-user-guide
docs/add-camera-troubleshooting
```

---

## Security Contribution Rules

SafeDesk includes security-sensitive workflows. Please follow these rules strictly.

Do not submit contributions that:

* Hardcode credentials.
* Commit `.env` files.
* Commit local configuration files.
* Commit owner face images.
* Commit intruder images.
* Commit SQLite databases.
* Commit runtime logs.
* Enable real shutdown by default.
* Enable real input blocking by default.
* Remove panic/recovery access.
* Remove safe test mode.
* Remove crash recovery or watchdog behavior.
* Add hidden persistence or stealth behavior.
* Exfiltrate images, logs, credentials, or user data.
* Send data to cloud services without explicit user configuration.
* Make SafeDesk behave like malware or spyware.

Any contribution touching lockdown, shutdown, authentication, intruder capture, or secrets handling must prioritize safety and owner control.

---

## Safe Test Mode Requirement

Features that involve dangerous or disruptive behavior must support demo/safe test mode first.

This includes:

* Shutdown escalation.
* Input lockdown.
* Email alerting.
* Alarm behavior.
* Forceful access detection.
* Threat-level escalation.

Real shutdown, real lockdown, and real email delivery should never be enabled by default.

---

## Coding Standards

Please follow these standards:

* Follow Python PEP 8 guidelines.
* Use clear naming.
* Add comments where logic is security-sensitive.
* Add docstrings to important functions/classes.
* Keep modules focused and maintainable.
* Avoid hardcoded absolute paths.
* Avoid global mutable state where possible.
* Keep secrets out of source code.
* Use meaningful commit messages.

---

## Testing Guidelines

Before submitting a pull request, test the relevant workflow.

Recommended checks:

* `python main.py`
* Configuration loading tests.
* Setup wizard validation tests.
* Authentication tests.
* Demo/safe test mode tests.
* No private files in `git status`.
* No credentials in committed files.
* No owner/intruder images committed.
* No SQLite databases committed.

If your change affects security behavior, explain how it was tested.

---

## Pull Request Checklist

Before submitting a pull request, confirm:

* [ ] My code follows the project style.
* [ ] I have tested my changes.
* [ ] I have not committed credentials.
* [ ] I have not committed private local config files.
* [ ] I have not committed owner/intruder images.
* [ ] I have not committed logs or databases.
* [ ] I have not enabled real shutdown by default.
* [ ] I have not enabled real lockdown by default.
* [ ] I have preserved safe test mode.
* [ ] I have preserved panic/recovery access.
* [ ] I have updated documentation if needed.
* [ ] I agree to the SafeDesk CLA.

---

## Need Help?

If you have questions, open an issue on GitHub or contact:

[studiyash@gmail.com](mailto:studiyash@gmail.com)

---

## Thank You

Thank you for helping improve SafeDesk. Your contributions help make the project safer, cleaner, and more useful.
