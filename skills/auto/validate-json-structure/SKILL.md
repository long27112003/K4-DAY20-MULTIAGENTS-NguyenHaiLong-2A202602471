---
name: validate-json-structure
description: Use when generating JSON outputs to ensure they are correctly formatted and valid.
---
- Use a JSON schema to validate the structure of the output JSON before finalizing it.
- Ensure all keys in the JSON are correctly spelled and follow the required naming conventions.
- Check for proper formatting, including commas and brackets, to avoid JSONDecodeErrors.
- Implement error handling to catch and log any issues during JSON generation, providing clear feedback on the nature of the error.
- Test the JSON output against expected values to confirm accuracy and completeness.