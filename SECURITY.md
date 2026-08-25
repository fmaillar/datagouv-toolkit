# Security Policy

## Supported versions

`datagouv-toolkit` is currently in early development. Security fixes are applied to the latest version on the `master` branch.

| Version | Supported |
| --- | --- |
| `master` | Yes |
| `v0.1.x` | Best effort |
| Older versions | No |

## Reporting a vulnerability

Please do **not** open a public GitHub issue for a suspected security vulnerability.

Use GitHub's private vulnerability reporting feature for this repository when available. If private reporting is not available, contact the maintainer privately through the contact information associated with the GitHub account.

When reporting a vulnerability, include as much of the following as possible:

- the affected file, command, or component;
- the version, tag, or commit tested;
- steps to reproduce the issue;
- the expected and actual behavior;
- the potential security impact;
- a minimal proof of concept, if applicable;
- any suggested mitigation or fix.

Do not include real secrets, access tokens, credentials, or sensitive third-party data in a report.

## Scope

Security reports are especially useful for issues involving:

- unsafe handling of downloaded files or paths;
- command or argument injection;
- arbitrary file overwrite or path traversal;
- insecure temporary-file handling;
- unintended disclosure of credentials or local data;
- unsafe HTTP or API behavior;
- dependency vulnerabilities that are directly exploitable through this project.

Data quality issues, incorrect statistics, feature requests, and ordinary bugs should be reported through normal GitHub issues instead.

## Disclosure process

Please allow reasonable time to investigate and prepare a fix before publicly disclosing a vulnerability. Once a fix is available, the affected versions and remediation steps may be documented in a GitHub security advisory or release notes.

## Security expectations

This project interacts with remote datasets and may download files from URLs supplied by data.gouv.fr metadata. Users should review the provenance of datasets and resources before processing them, especially when working with untrusted publishers or external resource URLs.
