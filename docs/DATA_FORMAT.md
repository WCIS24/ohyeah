# DATA_FORMAT

Unified sample schema (JSON):

```
{
  "qid": "string",
  "query": "string",
  "answer": "string",
  "evidences": [
    {
      "text": "string",
      "doc_id": "string or null",
      "meta": {
        "evidence_id": 0
      }
    }
  ],
  "meta": {
    "source": {"any": "original fields"}
  }
}
```

Notes:
- `qid` is taken from dataset field `field_map.qid` or generated as `row_<index>`.
- `query` and `answer` come from `field_map.query` and `field_map.answer`.
- `evidences` is parsed from `field_map.evidences` and stored as a list of evidence dicts.
- `doc_id` is optional; when absent, it is set to null.
- `meta.source` preserves remaining original fields for traceability.
