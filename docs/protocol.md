# VFlex MIDI Protocol Reference

This document describes the custom application-level protocol that VFLEX power adapters use over MIDI.

> **Disclaimer:** This protocol was reverse-engineered by observing USB MIDI traffic between the vendor web application and the device. It is not an official specification.

---

## Transport

The device presents itself to the operating system as a USB MIDI device with the port name **"Werewolf vFlex"**. It exposes a single bidirectional MIDI I/O port.

All application-layer communication is carried inside standard MIDI messages. The vendor web application also sends a **MIDI Clock** heartbeat (`0xF8`) roughly every 6 seconds, though vflexctl does not send heartbeats.

---

## Encoding: Protocol Byte ↔ MIDI Message

The VFlex protocol operates at the byte level. Each **protocol byte** is transported as a **MIDI Note-On message** (status byte `0x90`) with the byte split into two nibbles:

```
Protocol byte:  [b7 b6 b5 b4  b3 b2 b1 b0]
                 ─────────────  ──────────
MIDI byte 2:       high nibble  (bits 7–4)
MIDI byte 3:       low  nibble  (bits 3–0)
```

So the MIDI triplet for a protocol byte `P` is:

```
(0x90, (P >> 4) & 0x0F, P & 0x0F)
```

And the reverse, reconstructing `P` from a MIDI triplet `(status, b2, b3)`:

```
P = (b2 << 4) | b3
```

---

## Frame Structure

Every command or response is wrapped in a **frame** delimited by two sentinel MIDI messages:

| Sentinel | MIDI triplet | Direction |
|---|---|---|
| Start-of-frame | `(0x80, 0, 0)` | both |
| End-of-frame | `(0xA0, 0, 0)` | both |

A complete on-wire frame looks like:

```
(0x80, 0, 0)          ← start sentinel
(0x90, <hi>, <lo>)    ← protocol byte 0  (length)
(0x90, <hi>, <lo>)    ← protocol byte 1  (command)
(0x90, <hi>, <lo>)    ← protocol byte 2  (data byte 0)
…
(0xA0, 0, 0)          ← end sentinel
```

### Protocol Message Structure

After stripping the sentinels and converting MIDI triplets back to bytes, the resulting **protocol message** is a flat list of integers:

```
[ length, command, data_0, data_1, … ]
```

- **`length`** (byte 0) — the total number of bytes in the message, *including itself*. A single-byte command is represented as `[2, command]`.
- **`command`** (byte 1) — identifies the operation (see command table below).
- **`data_*`** (bytes 2 … length-1) — command-specific payload.

---

## Command Reference

### Command Bytes

| Constant | Hex | Dec | Direction | Description |
|---|---|---|---|---|
| `CMD_GET_SERIAL_NUMBER` | `0x08` | 8 | host→device | Request device serial number |
| `CMD_GET_LED_STATE` | `0x0F` | 15 | host→device | Request current LED behaviour |
| `CMD_SET_LED_STATE` | `0x8F` | 143 | host→device | Set LED behaviour |
| `CMD_GET_VOLTAGE` | `0x12` | 18 | host→device | Request current output voltage |
| `CMD_SET_VOLTAGE` | `0x92` | 146 | host→device | Set output voltage |

The set commands follow the convention `SET = GET | 0x80`.

---

### GET_SERIAL_NUMBER (`0x08`)

**Request** (host → device):

```
Protocol bytes: [2, 0x08]
```

Encoded as MIDI:

```
(0x80, 0, 0)        ← start
(0x90, 0, 2)        ← length = 2
(0x90, 0, 8)        ← command = 0x08
(0xA0, 0, 0)        ← end
```

**Response** (device → host):

```
Protocol bytes: [10, 0x08, c0, c1, c2, c3, c4, c5, c6, c7]
```

- Total length: 10 bytes.
- Bytes 2–9: 8 ASCII characters of the serial number (e.g. `"A1B2C3D4"`).

---

### GET_LED_STATE (`0x0F`)

**Request**:

```
Protocol bytes: [2, 0x0F]
```

**Response**:

```
Protocol bytes: [3, 0x0F, state]
```

- Total length: 3 bytes.
- `state`: `0x00` → LED is **always on** (factory default); `0x01` → LED is **disabled during normal operation**.

---

### SET_LED_STATE (`0x8F`)

**Request**:

```
Protocol bytes: [3, 0x8F, state]
```

- `state`: `0x00` for always-on; `0x01` for disabled.

**Response**: The device does not echo a confirmation for this command. After sending, the host must send a `GET_LED_STATE` request to confirm the new state.

---

### GET_VOLTAGE (`0x12`)

**Request**:

```
Protocol bytes: [2, 0x12]
```

**Response**:

```
Protocol bytes: [4, 0x12, high_byte, low_byte]
```

- Total length: 4 bytes.
- `high_byte`, `low_byte`: big-endian 16-bit unsigned integer in **millivolts**.

#### Millivolt Encoding

```
millivolts = (high_byte << 8) | low_byte
```

Examples:

| Voltage | Millivolts | high_byte | low_byte |
|---|---|---|---|
| 5 V | 5000 | 0x13 (19) | 0x88 (136) |
| 12 V | 12000 | 0x2E (46) | 0xE0 (224) |
| 12.5 V | 12500 | 0x30 (48) | 0xD4 (212) |
| 48 V | 48000 | 0xBB (187) | 0x80 (128) |

---

### SET_VOLTAGE (`0x92`)

**Request**:

```
Protocol bytes: [4, 0x92, high_byte, low_byte]
```

- `high_byte`, `low_byte`: desired output voltage in millivolts (big-endian 16-bit).

**Response**: The device echoes back the newly-set voltage in the same format as a `GET_VOLTAGE` response:

```
Protocol bytes: [4, 0x12, high_byte, low_byte]
```

Note: the response uses the *get* command byte (`0x12`), not the *set* byte.

---

## Timing

All timing constants are empirical:

| Constant | Value | Location | Purpose |
|---|---|---|---|
| `DEFAULT_PAUSE_LENGTH` | 2 ms | `midi_transport/senders.py` | Pause between each MIDI message in a sequence |
| `drain_incoming` default `seconds` | 500 ms | `midi_transport/receivers.py` | Time window for reading device responses |

The 2 ms inter-message pause prevents the device from dropping messages when commands are sent in rapid succession. The 500 ms drain window gives the device sufficient time to process a command and stream its response back.

---

## Full Worked Example — Set Voltage to 12 V

### 1. Compute millivolts

```
12 V × 1000 = 12000 mV
high_byte = (12000 >> 8) & 0xFF = 0x2E
low_byte  =  12000       & 0xFF = 0xE0
```

### 2. Build protocol message

```
Command sub-message: [CMD_SET_VOLTAGE, 0x2E, 0xE0]
                   = [0x92,             0x2E, 0xE0]

Add length prefix:  [4, 0x92, 0x2E, 0xE0]
```

### 3. Encode as MIDI triplets

| Protocol byte | Hex | MIDI triplet |
|---|---|---|
| length = 4 | `0x04` | `(0x90, 0x00, 0x04)` |
| command = 0x92 | `0x92` | `(0x90, 0x09, 0x02)` |
| high = 0x2E | `0x2E` | `(0x90, 0x02, 0x0E)` |
| low = 0xE0 | `0xE0` | `(0x90, 0x0E, 0x00)` |

### 4. Wrap in frame

```
(0x80, 0x00, 0x00)   ← start
(0x90, 0x00, 0x04)   ← length
(0x90, 0x09, 0x02)   ← command
(0x90, 0x02, 0x0E)   ← high byte
(0x90, 0x0E, 0x00)   ← low byte
(0xA0, 0x00, 0x00)   ← end
```

### 5. Device response (confirmation)

The device replies with the confirmed voltage encoded as `GET_VOLTAGE`:

```
(0x80, 0x00, 0x00)   ← start
(0x90, 0x00, 0x04)   ← length = 4
(0x90, 0x01, 0x02)   ← command = 0x12 (GET_VOLTAGE)
(0x90, 0x02, 0x0E)   ← high = 0x2E
(0x90, 0x0E, 0x00)   ← low  = 0xE0
(0xA0, 0x00, 0x00)   ← end
```

Decoded: `(0x2E << 8) | 0xE0 = 11776 + 224 = 12000 mV = 12 V ✓`
