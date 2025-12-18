# MCP Tools (MCP surface)

`mcp-browser` exposes a small, consolidated MCP tool surface optimized for AI coding assistants.

## Tool list (current)

As implemented in `src/services/mcp_service.py`, the server exposes 5 tools:

1. `browser_action` — browser actions (`navigate`, `click`, `fill`, `select`, `wait`)
2. `browser_query` — queries (`logs`, `element`, `capabilities`)
3. `browser_screenshot` — capture a screenshot
4. `browser_form` — form operations (`fill`, `submit`)
5. `browser_extract` — content extraction (`content`, `semantic_dom`)

### Ports and daemons

- The `port` argument is optional for all tools.
- If `port` is omitted, `mcp-browser` attempts to auto-detect the active WebSocket daemon for the current project.
- For extension-backed features, start the daemon in a separate terminal: `mcp-browser start --background`.

## Schemas and common usage

### `browser_action`

Use for navigation and single-step interactions.

Required:
- `action`: one of `navigate | click | fill | select | wait`

Common fields:
- `port` (optional)
- `url` (for `navigate`)
- `selector` / `xpath` (for element targeting)
- `text` (for `click`)
- `index` (optional, default `0`)
- `value` (for `fill`)
- `option_value` / `option_text` / `option_index` (for `select`)
- `timeout` (ms, for `wait`, default `5000`)

Examples:
```json
{"action":"navigate","url":"https://example.com"}
```
```json
{"action":"click","selector":"button[type='submit']"}
```
```json
{"action":"fill","selector":"#email","value":"test@example.com"}
```

### `browser_query`

Use for retrieving logs, element info, or runtime capabilities.

Required:
- `query`: one of `logs | element | capabilities`

Common fields:
- `port` (optional)
- `last_n` (for `logs`, default `100`)
- `level_filter` (for `logs`: `debug|info|log|warn|error`)
- `selector` / `xpath` / `text` (for `element`)

Examples:
```json
{"query":"logs","last_n":50,"level_filter":["error","warn"]}
```
```json
{"query":"element","selector":"#login-form"}
```

### `browser_screenshot`

Captures a screenshot of the current browser viewport.

Fields:
- `port` (optional)
- `url` (optional: navigate before capture)

Example:
```json
{"url":"https://example.com"}
```

### `browser_form`

Use for multi-field fills or form submission.

Required:
- `action`: one of `fill | submit`

Common fields:
- `port` (optional)
- `form_data` (for `fill`: object mapping selectors → values)
- `submit` (for `fill`: boolean, default `false`)
- `selector` / `xpath` (for `submit`)

Example:
```json
{"action":"fill","form_data":{"#email":"test@example.com","#password":"secret"},"submit":true}
```

### `browser_extract`

Extracts readable content, a semantic DOM summary, or an ASCII box diagram.

Required:
- `extract`: one of `content | semantic_dom | ascii`

Common fields:
- `port` (optional)
- `tab_id` (optional)

#### Extract Types

| Type | Description |
|------|-------------|
| `content` | Readable text content from page |
| `semantic_dom` | Semantic DOM summary with structure |
| `ascii` | ASCII box diagram showing element positions |

#### semantic_dom Options

- `include_headings` / `include_landmarks` / `include_links` / `include_forms` (boolean)
- `max_text_length` (integer)

#### ascii Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ascii_width` | integer | 80 | Output width in characters |
| `max_text_length` | integer | 20 | Max text length per element label |

**Output includes:**
- Viewport dimensions
- Box diagram of visible page elements
- Element type legend with counts
- Page URL and title

**Best for:**
- Quick visual hierarchy understanding
- Token-efficient layout visualization (~100x smaller than screenshots)
- Understanding element spatial relationships
- Layout debugging without images

#### Examples

**Example - Semantic DOM:**
```json
{"extract":"semantic_dom","include_headings":true,"include_links":true,"max_text_length":120}
```

**Example - ASCII Layout:**
```json
{"extract":"ascii","ascii_width":100,"max_text_length":20,"port":8851}
```

## Migration from legacy tool names

Older documentation may reference a larger set of fine-grained tools. Use this mapping:

| Legacy tool | Replacement |
|---|---|
| `browser_navigate` | `browser_action` with `{"action":"navigate","url":...}` |
| `browser_click` | `browser_action` with `{"action":"click", ...}` |
| `browser_fill_field` | `browser_action` with `{"action":"fill","value":...}` |
| `browser_select_option` | `browser_action` with `{"action":"select", ...}` |
| `browser_wait_for_element` | `browser_action` with `{"action":"wait","timeout":...}` |
| `browser_query_logs` | `browser_query` with `{"query":"logs","last_n":...}` |
| `browser_get_element` | `browser_query` with `{"query":"element", ...}` |
| `browser_fill_form` | `browser_form` with `{"action":"fill","form_data":...}` |
| `browser_submit_form` | `browser_form` with `{"action":"submit", ...}` |
| `browser_extract_content` | `browser_extract` with `{"extract":"content"}` |
| `browser_extract_semantic_dom` | `browser_extract` with `{"extract":"semantic_dom"}` |

