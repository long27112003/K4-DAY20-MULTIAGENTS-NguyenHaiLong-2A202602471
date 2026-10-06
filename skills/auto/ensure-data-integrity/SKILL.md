---
name: ensure-data-integrity
description: Use when processing data to maintain accuracy and compliance with data standards.
---
- Validate all monetary values are represented in integer cents, converting from decimal formats as necessary.
- Ensure the output JSON structure includes a `meta` object with `source`, `rows_in`, and `rows_used` fields.
- Clean input CSV files by removing duplicate rows and ensuring all data adheres to the specified schema.
- Format timestamps in UTC as YYYY-MM-DDTHH:MM:SSZ and ensure region names are in canonical spelling (North, South, East, West).
- Handle missing amounts appropriately, ensuring they are excluded from calculations and reported correctly.