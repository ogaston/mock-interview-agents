import pathlib


def generate_mock_audio_bytes() -> bytes:
    """
    Read and return the example.mp3 audio file bytes.
    This provides a real MP3 audio file for mock TTS responses.
    """
    # Get the path to example.mp3 in the same directory
    current_dir = pathlib.Path(__file__).parent
    audio_file = current_dir / "example.mp3"
    
    # Read and return the audio file bytes
    with open(audio_file, "rb") as f:
        return f.read()
