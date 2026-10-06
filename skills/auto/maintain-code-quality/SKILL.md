---
name: maintain-code-quality
description: Use when modifying code to ensure compliance with coding standards and documentation.
---
- Ensure all code changes adhere to the project's coding standards, including proper syntax and formatting.
- Avoid modifying existing test files; create new tests as needed to cover changes.
- Validate that all f-string expressions are correctly formatted without backslashes.
- Implement regression tests for each bug fix, ensuring at least three tests are added to a dedicated regression test file.
- Document all changes in the CHANGELOG.md under the '## Unreleased' section, using the format: '- fix(<function name>): <short description>'.
- Review and update docstrings to reflect any changes in function behavior or parameters.