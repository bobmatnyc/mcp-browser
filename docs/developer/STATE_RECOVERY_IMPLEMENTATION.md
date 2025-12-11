# State Recovery Handshake Protocol Implementation

## Overview
This document describes the implementation of the State Recovery Handshake Protocol in the mcp-browser backend.

## Implementation Details

### 1. Message Buffer (`deque`)
- **Location**: `websocket_service.py` line 38
- **Type**: `collections.deque`
- **Max Length**: 1000 messages
- **Purpose**: Stores recent messages for replay on reconnection

```python
self.message_buffer: deque = deque(maxlen=1000)  # Keep last 1000 messages
```

### 2. Sequence Counter
- **Location**: `websocket_service.py` line 39
- **Type**: `int`
- **Purpose**: Tracks current sequence number across all messages

```python
self.current_sequence: int = 0
```

### 3. Connection Init Handler
- **Location**: `websocket_service.py` lines 102-135
- **Method**: `handle_connection_init(message, websocket)`
- **Purpose**: Handles connection initialization handshake from extension

**Workflow**:
1. Extracts `lastSequence`, `extensionVersion`, and `capabilities` from message
2. Logs connection information
3. Retrieves missed messages using `_get_messages_after_sequence()`
4. Imports server version from `_version.py`
5. Sends `connection_ack` with replay messages (max 100)

**Example `connection_ack` Response**:
```json
{
  "type": "connection_ack",
  "serverVersion": "2.1.1",
  "currentSequence": 42,
  "replay": [
    {"type": "console_log", "sequence": 40, "data": "..."},
    {"type": "console_log", "sequence": 41, "data": "..."}
  ]
}
```

### 4. Message Replay Helper
- **Location**: `websocket_service.py` lines 137-149
- **Method**: `_get_messages_after_sequence(last_sequence)`
- **Purpose**: Filters buffered messages to find those after a given sequence

```python
def _get_messages_after_sequence(self, last_sequence: int) -> List[dict]:
    return [
        msg for msg in self.message_buffer
        if msg.get('sequence', 0) > last_sequence
    ]
```

### 5. Sequence Addition Helper
- **Location**: `websocket_service.py` lines 151-163
- **Method**: `_add_sequence(message)`
- **Purpose**: Adds sequence number to message and buffers it

**Workflow**:
1. Increments `current_sequence`
2. Adds `sequence` field to message
3. Appends copy to `message_buffer`
4. Returns sequenced message

```python
def _add_sequence(self, message: dict) -> dict:
    self.current_sequence += 1
    message['sequence'] = self.current_sequence
    self.message_buffer.append(message.copy())
    return message
```

### 6. Message Routing
- **Location**: `websocket_service.py` lines 222-225
- **Purpose**: Routes `connection_init` messages to handler

```python
if message_type == "connection_init":
    await self.handle_connection_init(data, websocket)
    return
```

### 7. Updated send_message
- **Location**: `websocket_service.py` lines 269-284
- **New Parameter**: `add_sequence: bool = False`
- **Purpose**: Optionally adds sequence number when sending messages

**Usage Example**:
```python
# For replayable messages (console logs, DOM responses)
await self.send_message(websocket, {
    'type': 'console_log',
    'data': log_data
}, add_sequence=True)

# For non-replayable messages (pong, ack)
await self.send_message(websocket, {
    'type': 'pong',
    'timestamp': timestamp
})
```

## Protocol Flow

### Extension Connection
1. Extension connects to WebSocket server
2. Extension sends `connection_init`:
   ```json
   {
     "type": "connection_init",
     "lastSequence": 42,
     "extensionVersion": "1.0.0",
     "capabilities": ["console", "dom"]
   }
   ```
3. Server receives `connection_init`
4. Server finds missed messages (sequence > 42)
5. Server sends `connection_ack` with replay:
   ```json
   {
     "type": "connection_ack",
     "serverVersion": "2.1.1",
     "currentSequence": 100,
     "replay": [...]  // Max 100 messages
   }
   ```
6. Extension processes replay and updates state

### Message Sequencing
- Only messages marked with `add_sequence=True` are buffered
- Typical sequenced messages:
  - `console_log` - Console output from browser
  - `dom_response` - DOM query results
  - `dom_update` - DOM change notifications
- Non-sequenced messages:
  - `pong` - Heartbeat responses
  - `connection_ack` - Handshake responses
  - `server_info_response` - Server metadata

## Testing

### Unit Tests
Run the test suite to verify implementation:
```bash
python test_state_recovery.py
```

**Tests Cover**:
1. ✓ Message buffer initialization (deque, maxlen=1000)
2. ✓ Sequence numbering (incremental, accurate)
3. ✓ Message replay (filtering by sequence)
4. ✓ Connection init message structure
5. ✓ Connection ack response structure
6. ✓ Buffer limit enforcement (1000 messages)

### Integration Testing
1. Start the MCP server
2. Open Chrome DevTools → Network tab
3. Reload the extension
4. Check server logs for:
   ```
   INFO: Connection init from extension v1.0.0, lastSequence=0
   INFO: Client capabilities: ['console', 'dom']
   INFO: Sent connection_ack with 0 replayed messages
   ```
5. Disconnect and reconnect
6. Verify replay messages in logs:
   ```
   INFO: Connection init from extension v1.0.0, lastSequence=42
   INFO: Sent connection_ack with 5 replayed messages
   ```

## Success Criteria

✅ **All criteria met**:
- [x] message_buffer deque added (maxlen=1000)
- [x] current_sequence counter added
- [x] handle_connection_init method implemented
- [x] _get_messages_after_sequence method implemented
- [x] _add_sequence method implemented
- [x] connection_init message type routed correctly
- [x] connection_ack sent with replay messages
- [x] No syntax errors
- [x] All unit tests pass

## Usage Guidelines

### For Message Senders
When sending messages that should be recoverable on reconnect:

```python
# Replayable message
await websocket_service.send_message(websocket, {
    'type': 'console_log',
    'level': 'info',
    'message': 'Application started'
}, add_sequence=True)
```

### For Message Handlers
Message handlers don't need to change - they receive messages as before, with an optional `sequence` field added.

### Buffer Management
- Buffer automatically maintains last 1000 messages
- Oldest messages are dropped when buffer is full
- Sequence numbers continue incrementing (never reset)
- Replay is limited to max 100 messages to prevent bandwidth issues

## Future Enhancements

1. **Persistent Storage**: Store message buffer to disk for recovery after server restart
2. **Configurable Buffer Size**: Allow buffer size configuration via environment variable
3. **Message Prioritization**: Replay critical messages first (errors before logs)
4. **Compression**: Compress replay messages to reduce bandwidth
5. **Selective Replay**: Allow extension to request specific message types

## Related Files

- `/Users/masa/Projects/mcp-browser/src/services/websocket_service.py` - Implementation
- `/Users/masa/Projects/mcp-browser/test_state_recovery.py` - Unit tests
- `/Users/masa/Projects/mcp-browser/src/_version.py` - Version info

## Version
- Implementation Date: 2025-12-11
- Server Version: 2.1.1
- Protocol Version: 1.0
