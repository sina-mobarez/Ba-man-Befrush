# Ba-man-Befrush

## Persian AI Content Generation Bot

A Telegram bot for generating Persian content for jewelry businesses with AI-powered speech-to-text capabilities.

### 🎤 NEW: Persian Speech-to-Text Feature

This bot now supports Persian voice messages with high-quality speech recognition:

- **Model**: `vhdm/whisper-large-fa-v1` - Fine-tuned Whisper Large V3 for Persian
- **Accuracy**: Word Error Rate of 14.07%
- **Language Support**: All Persian accents and dialects
- **Integration**: Seamless voice input for all content generation features

### Features

- 🧠 **AI Content Generation**: Captions, Reels scenarios, Visual ideas
- 🎤 **Voice Input**: Send voice messages instead of typing
- 📱 **User Profiles**: Personalized content based on business style
- 💎 **Jewelry Focus**: Specialized for jewelry and gold businesses
- 🔁 **Subscription Management**: Trial and paid plans

### Voice Message Workflow

1. User sends voice message in any content generation state
2. Automatic transcription using Persian Whisper model
3. User confirms or edits transcribed text
4. Content generated based on voice input

### Requirements

- Python 3.10+
- PyTorch (for speech recognition)
- Transformers library
- Audio processing libraries (librosa, pydub)

### Installation

```bash
pip install -r requirements.txt
```

### Environment Variables

```bash
# Speech-to-Text Settings (Optional)
WHISPER_MODEL_NAME=vhdm/whisper-large-fa-v1
AUDIO_MAX_FILE_SIZE_MB=20
AUDIO_MAX_DURATION_SECONDS=300
```

### Usage

Users can:
- Send voice messages for content requests
- Use traditional text input
- Switch between voice and text seamlessly
- Get transcription confirmation before content generation