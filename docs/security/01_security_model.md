# Security & Untrusted Input Model

1. **Untrusted Input Wrapping**: External emails and uploaded attachments are processed inside strict delimiter tags (`<untrusted_content>`) to mitigate prompt injection.
2. **Secrets & OAuth Storage**: OAuth tokens and API secrets must be encrypted at rest and never checked into source control.
3. **Human Approval**: High-impact actions (such as sending emails) require manual review and confirmation by the user.
