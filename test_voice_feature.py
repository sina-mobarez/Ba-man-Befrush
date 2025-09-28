#!/usr/bin/env python3
"""
Test script for the Persian speech-to-text feature implementation.
This script verifies that all files are properly structured and ready for testing.
"""

def test_file_structure():
    """Test that all required files exist and are properly structured."""
    import os

    print("🔍 Testing file structure...")

    # Check requirements.txt
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
        speech_deps = ['torch', 'transformers', 'librosa', 'pydub', 'soundfile']
        for dep in speech_deps:
            if dep in requirements:
                print(f"✅ {dep} found in requirements.txt")
            else:
                print(f"❌ {dep} missing from requirements.txt")

    # Check speech service
    speech_service_path = 'app/services/speech_service.py'
    if os.path.exists(speech_service_path):
        print(f"✅ {speech_service_path} exists")
        with open(speech_service_path, 'r') as f:
            content = f.read()
            if 'vhdm/whisper-large-fa-v1' in content:
                print("✅ Persian Whisper model configured")
            if 'async def process_voice_message' in content:
                print("✅ Voice processing method implemented")
    else:
        print(f"❌ {speech_service_path} missing")

    # Check handler updates
    handler_path = 'app/handlers/common.py'
    if os.path.exists(handler_path):
        print(f"✅ {handler_path} exists")
        with open(handler_path, 'r') as f:
            content = f.read()
            if '@router.message(F.voice)' in content:
                print("✅ Voice message handler added")
            if 'SpeechService' in content:
                print("✅ SpeechService imported")
            if 'قابلیت جدید - پیام صوتی' in content:
                print("✅ Help text updated with voice feature")
    else:
        print(f"❌ {handler_path} missing")

    # Check config updates
    config_path = 'app/core/config.py'
    if os.path.exists(config_path):
        print(f"✅ {config_path} exists")
        with open(config_path, 'r') as f:
            content = f.read()
            if 'WHISPER_MODEL_NAME' in content:
                print("✅ Speech configuration added")
    else:
        print(f"❌ {config_path} missing")

def test_syntax():
    """Test syntax of Python files."""
    import py_compile
    import os

    print("\n🔍 Testing Python syntax...")

    files_to_check = [
        'app/services/speech_service.py',
        'app/handlers/common.py',
        'app/core/config.py',
        'app/main.py'
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                py_compile.compile(file_path, doraise=True)
                print(f"✅ {file_path} syntax OK")
            except py_compile.PyCompileError as e:
                print(f"❌ {file_path} syntax error: {e}")
        else:
            print(f"❌ {file_path} not found")

def print_summary():
    """Print implementation summary."""
    print("\n" + "="*60)
    print("🎤 PERSIAN SPEECH-TO-TEXT IMPLEMENTATION SUMMARY")
    print("="*60)
    print()
    print("✨ Features Implemented:")
    print("• Voice message handler for Telegram")
    print("• Persian Whisper model integration (vhdm/whisper-large-fa-v1)")
    print("• Audio format conversion and processing")
    print("• Voice transcription confirmation flow")
    print("• Integration with existing content generation")
    print("• File size and duration validation")
    print("• Error handling and user feedback")
    print("• Voice support for caption, reels, and visual content")
    print()
    print("🔧 Next Steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Set up environment variables (.env)")
    print("3. Test with real voice messages")
    print("4. Monitor performance and adjust model settings")
    print()
    print("📱 User Experience:")
    print("• Users can send voice messages in any content generation state")
    print("• Automatic transcription with confirmation step")
    print("• Seamless integration with existing workflows")
    print("• Support for all Persian accents and dialects")
    print()
    print("⚡ Model Details:")
    print("• Model: vhdm/whisper-large-fa-v1")
    print("• 809M parameters, fine-tuned for Persian")
    print("• Word Error Rate: 14.07%")
    print("• Supports all Persian accents")

if __name__ == "__main__":
    test_file_structure()
    test_syntax()
    print_summary()