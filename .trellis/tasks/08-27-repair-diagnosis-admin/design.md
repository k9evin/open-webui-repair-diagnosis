# Design

Reuse the existing workspace/admin page patterns and the repair API. The importer parses XLSX synchronously for the MVP, produces a preview/result object before committing, and stores each source row unchanged. SOP and review screens use simple forms and table/list controls; no generic admin framework is added.
