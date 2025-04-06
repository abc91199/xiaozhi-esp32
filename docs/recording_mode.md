# Recording Mode Implementation

This document describes how the recording mode is triggered and released in the XiaoZhi AI Chatbot firmware.

## Overview

The recording mode is implemented through a combination of hardware and software components:

1. Audio Codec Hardware Control
2. Application State Management
3. Protocol Communication

## Audio Codec Control

The audio input is controlled through the `EnableInput(bool enable)` method in the `AudioCodec` class hierarchy. This method is implemented by various audio codec classes:

- `BoxAudioCodec`
- `Es8311AudioCodec`
- `Es8388AudioCodec`
- `SensecapAudioCodec`
- `K10AudioCodec`
- `Tcamerapluss3AudioCodec`
- `Tcircles3AudioCodec`
- `CoreS3AudioCodec`

Each implementation handles the specific hardware requirements for enabling/disabling the microphone input.

## Application State Management

The recording mode is managed by the `Application` class through two main methods:

### StartListening()

Located in `main/application.cc`:
```cpp
void Application::StartListening() {
    if (device_state_ == kDeviceStateActivating) {
        SetDeviceState(kDeviceStateIdle);
        return;
    }

    if (!protocol_) {
        ESP_LOGE(TAG, "Protocol not initialized");
        return;
    }
    
    keep_listening_ = false;
    if (device_state_ == kDeviceStateIdle) {
        Schedule([this]() {
            if (!protocol_->IsAudioChannelOpened()) {
                SetDeviceState(kDeviceStateConnecting);
                if (!protocol_->OpenAudioChannel()) {
                    return;
                }
            }
            protocol_->SendStartListening(kListeningModeManualStop);
            SetDeviceState(kDeviceStateListening);
        });
    } else if (device_state_ == kDeviceStateSpeaking) {
        Schedule([this]() {
            AbortSpeaking(kAbortReasonNone);
            protocol_->SendStartListening(kListeningModeManualStop);
            SetDeviceState(kDeviceStateListening);
        });
    }
}
```

### StopListening()

Located in `main/application.cc`:
```cpp
void Application::StopListening() {
    Schedule([this]() {
        if (device_state_ == kDeviceStateListening) {
            protocol_->SendStopListening();
            SetDeviceState(kDeviceStateIdle);
        }
    });
}
```

## Protocol Communication

The recording mode is communicated to the server through the `Protocol` class:

### SendStartListening()

Located in `main/protocols/protocol.cc`:
```cpp
void Protocol::SendStartListening(ListeningMode mode) {
    std::string message = "{\"session_id\":\"" + session_id_ + "\"";
    message += ",\"type\":\"listen\",\"state\":\"start\"";
    if (mode == kListeningModeAlwaysOn) {
        message += ",\"mode\":\"realtime\"";
    } else if (mode == kListeningModeAutoStop) {
        message += ",\"mode\":\"auto\"";
    } else {
        message += ",\"mode\":\"manual\"";
    }
    message += "}";
    SendText(message);
}
```

### SendStopListening()

Located in `main/protocols/protocol.cc`:
```cpp
void Protocol::SendStopListening() {
    std::string message = "{\"session_id\":\"" + session_id_ + "\",\"type\":\"listen\",\"state\":\"stop\"}";
    SendText(message);
}
```

## Listening Modes

There are three listening modes defined in `main/protocols/protocol.h`:

```cpp
enum ListeningMode {
    kListeningModeAutoStop,    // Automatically stops after silence
    kListeningModeManualStop,  // Requires explicit stop command
    kListeningModeAlwaysOn     // Continuous listening (requires AEC support)
};
```

## Trigger Points

The recording mode can be triggered from several places in the codebase:

1. **Button Press**: Various board implementations call `StartListening()` and `StopListening()` in response to button presses
2. **Wake Word Detection**: When a wake word is detected, the system automatically starts listening
3. **Protocol Commands**: The server can send commands to start/stop listening

## State Transitions

The recording mode is part of the device's state machine:

1. `kDeviceStateIdle` → `kDeviceStateConnecting` → `kDeviceStateListening`
2. `kDeviceStateSpeaking` → `kDeviceStateListening`
3. `kDeviceStateListening` → `kDeviceStateIdle`

## Audio Channel Management

Before recording can start, an audio channel must be established:

1. The system checks if an audio channel is already open
2. If not, it attempts to open a new channel
3. Only after the channel is established can recording begin

## Error Handling

The implementation includes several error checks:

1. Protocol initialization check
2. Audio channel availability check
3. State transition validation
4. Hardware initialization verification 