/**
 * Audio Service - API client for voice features
 * Handles TTS (text-to-speech) and STT (speech-to-text) operations
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export interface TranscribeResponse {
    text: string;
}

export interface SynthesizeRequest {
    text: string;
    voice_id?: string;
}

// Keep track of the currently playing audio to allow interruption
let currentAudio: HTMLAudioElement | null = null;

/**
 * Stop any currently playing audio
 */
export function stopAudio(): void {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }
}

/**
 * Transcribe audio to text using backend STT API
 */
export async function transcribeAudio(audioBlob: Blob): Promise<string> {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');

    const response = await fetch(`${API_BASE_URL}/api/audio/transcribe`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Transcription failed');
    }

    const data: TranscribeResponse = await response.json();
    return data.text;
}

/**
 * Synthesize text to speech using backend TTS API
 */
export async function synthesizeSpeech(
    text: string,
    voiceId?: string
): Promise<Blob> {
    const request: SynthesizeRequest = { text, voice_id: voiceId };

    const response = await fetch(`${API_BASE_URL}/api/audio/synthesize`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Speech synthesis failed');
    }

    return await response.blob();
}

/**
 * Play audio from a blob
 */
export function playAudio(audioBlob: Blob): Promise<void> {
    // Stop any existing audio first
    stopAudio();

    return new Promise((resolve, reject) => {
        const audio = new Audio(URL.createObjectURL(audioBlob));
        currentAudio = audio;
        
        audio.onended = () => {
            URL.revokeObjectURL(audio.src);
            if (currentAudio === audio) {
                currentAudio = null;
            }
            resolve();
        };
        
        audio.onerror = (error) => {
            URL.revokeObjectURL(audio.src);
            if (currentAudio === audio) {
                currentAudio = null;
            }
            reject(error);
        };
        
        audio.play().catch(reject);
    });
}

/**
 * Check if browser supports Web Speech API for STT
 */
export function isBrowserSTTSupported(): boolean {
    return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
}

/**
 * Create a browser-based speech recognition instance
 */
export function createBrowserSTT(): any | null {
    if (!isBrowserSTTSupported()) {
        return null;
    }

    const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    const recognition = new SpeechRecognition();
    recognition.continuous = true; // Changed to true for better flow
    recognition.interimResults = true; // Enable live partial results
    recognition.lang = 'en-US';

    return recognition;
}
