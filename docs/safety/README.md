# Safety

SafeDesk follows safety-first development because the project involves authentication, local private data, webcam-based verification, evidence capture, protected mode behavior, alerting, and eventual shutdown escalation.

Public safety documentation should explain the principles that guide the project:

- Real shutdown, real lockdown, and real email delivery must be controlled and disabled by default during development.
- Credentials, local secrets, and private configuration must never be committed.
- Owner images, intruder images, logs, databases, and runtime captures must stay local.
- Recovery and safe test behavior must be considered before disruptive protection features are enabled.
- Public documentation should help users understand safety expectations without becoming a bypass guide or full recreation guide.

Detailed internal safety workflows, escalation rules, testing notes for dangerous behavior, and recovery internals are intentionally kept out of public documentation.
