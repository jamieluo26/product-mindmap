# Map data contract

The schema is `interactive-mindmap/v1`. All example content in this package is invented.

Top-level fields:

| Field | Meaning |
|---|---|
| schema | Exact schema identifier above |
| rootId | HTML ID starting with a letter; then letters, digits or hyphens |
| edition, kind | Short strings of at most 50 characters |
| initialSelected | An existing node ID |
| initialExpanded | Array of existing node IDs |
| root | Root node with id `root`, and 1–8 main branches |

Each node has a unique `id` with the same ID character rules, `title` (1–30 characters), `status` (`confirmed`, `suggested` or `pending`), `facts` (a list of two-string label/text pairs), and `children` (a list). Optional `caption` is at most 40 characters. Optional `side` is `left` or `right` and is allowed only on a main branch immediately below the root. Maximum depth is 10 below the root; maximum node count is 200.

Confirmed means accepted or evidenced. Suggested means a proposal. Pending means unresolved. The renderer does not decide which status is true; the author must preserve the evidence boundary.

The builder validates shape and references, escapes HTML text fields, encodes script-sensitive JSON characters, and fails if a template token remains. It does not validate truth, accessibility or browser interactions. Use synthetic-map.json for a complete input example.
