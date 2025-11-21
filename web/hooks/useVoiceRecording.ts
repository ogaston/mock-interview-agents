/**
 * useVoiceRecording - Hook for managing voice recording and transcription
 * Supports both browser Web Speech API and backend OpenAI Whisper
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import {
    transcribeAudio,
    createBrowserSTT,
    isBrowserSTTSupported,
} from '@/services/audioService';

export type RecordingState = 'idle' | 'recording' | 'processing' | 'error';

export interface UseVoiceRecordingOptions {
    useBrowserSTT?: boolean; // Prefer browser Web Speech API
    autoStopTimeout?: number; // Auto-stop recording after N milliseconds of silence
    onTranscript?: (text: string) => void;
    onError?: (error: Error) => void;
}

export function useVoiceRecording(options: UseVoiceRecordingOptions = {}) {
    const {
        useBrowserSTT = true,
        autoStopTimeout = 3000,
        onTranscript,
        onError
    } = options;

    const [state, setState] = useState<RecordingState>('idle');
    const [transcript, setTranscript] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const speechRecognitionRef = useRef<any | null>(null);
    const autoStopTimerRef = useRef<NodeJS.Timeout | null>(null);

    /**
     * Clear auto-stop timer
     */
    const clearAutoStopTimer = useCallback(() => {
        if (autoStopTimerRef.current) {
            clearTimeout(autoStopTimerRef.current);
            autoStopTimerRef.current = null;
        }
    }, []);

    /**
     * Start recording audio
     */
    const startRecording = useCallback(async () => {
        try {
            setError(null);
            setTranscript(''); // Clear previous transcript
            setState('recording');

            // Try browser STT first if enabled and supported
            if (useBrowserSTT && isBrowserSTTSupported()) {
                const recognition = createBrowserSTT();
                if (recognition) {
                    speechRecognitionRef.current = recognition;

                    recognition.onresult = (event: any) => {
                        let finalTranscript = '';
                        let interimTranscript = '';

                        for (let i = event.resultIndex; i < event.results.length; ++i) {
                            if (event.results[i].isFinal) {
                                finalTranscript += event.results[i][0].transcript;
                            } else {
                                interimTranscript += event.results[i][0].transcript;
                            }
                        }

                        // Combine previous transcript with new results if needed,
                        // but simplest is to just show what the recognizer gives us 
                        // since we are using continuous=true.
                        // Note: React state updates might need care if appending, 
                        // but Web Speech API usually sends full session transcript if not careful.
                        // With continuous=true, we get new chunks.
                        
                        // Actually, a common pattern is to just use the latest interim result for display
                        const currentText = finalTranscript + interimTranscript;
                        console.log('Speech recognition result:', currentText);
                        setTranscript(currentText);
                        onTranscript?.(currentText);
                    };

                    recognition.onerror = (event: any) => {
                        console.error('Speech recognition error:', event.error);

                        // Don't treat "no-speech" as a critical error
                        if (event.error === 'no-speech') {
                            const err = new Error('No se detectó voz. Por favor intenta de nuevo.');
                            setError(err.message);
                            onError?.(err);
                            setState('idle');
                        } else {
                            const err = new Error(`Error de reconocimiento de voz: ${event.error}`);
                            setError(err.message);
                            onError?.(err);
                            setState('error');
                        }
                    };

                    recognition.onend = () => {
                        console.log('Speech recognition ended');
                        setState('idle');
                        clearAutoStopTimer();
                    };

                    // Browser STT automatically stops when user stops speaking
                    console.log('Starting browser speech recognition');
                    recognition.start();
                    return;
                }
            }

            // Fallback to MediaRecorder for backend transcription
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            setMediaStream(stream);
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                setState('processing');
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

                try {
                    const text = await transcribeAudio(audioBlob);
                    setTranscript(text);
                    onTranscript?.(text);
                    setState('idle');
                } catch (err) {
                    const error = err as Error;
                    setError(error.message);
                    onError?.(error);
                    setState('error');
                } finally {
                    // Stop all tracks
                    stream.getTracks().forEach((track) => track.stop());
                }
            };

            mediaRecorder.start();

            // Auto-stop after timeout for MediaRecorder
            if (autoStopTimeout > 0) {
                autoStopTimerRef.current = setTimeout(() => {
                    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                        console.log('Auto-stopping recording after timeout');
                        mediaRecorderRef.current.stop();
                    }
                }, autoStopTimeout);
            }
        } catch (err) {
            const error = err as Error;
            setError(error.message);
            onError?.(error);
            setState('error');
        }
    }, [useBrowserSTT, autoStopTimeout, onTranscript, onError, clearAutoStopTimer]);

    /**
     * Stop recording audio
     */
    const stopRecording = useCallback(() => {
        clearAutoStopTimer();

        if (speechRecognitionRef.current) {
            console.log('Stopping speech recognition');
            try {
                speechRecognitionRef.current.stop();
            } catch (e) {
                console.error('Error stopping speech recognition:', e);
            }
            speechRecognitionRef.current = null;
        }

        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            console.log('Stopping media recorder');
            mediaRecorderRef.current.stop();
        }
    }, [clearAutoStopTimer]);

    /**
     * Cancel recording
     */
    const cancelRecording = useCallback(() => {
        stopRecording();
        setState('idle');
        setTranscript('');
        setError(null);
    }, [stopRecording]);

    /**
     * Reset state
     */
    const reset = useCallback(() => {
        setTranscript('');
        setError(null);
        setState('idle');
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            clearAutoStopTimer();
            if (speechRecognitionRef.current) {
                try {
                    speechRecognitionRef.current.stop();
                } catch (e) {
                    // Ignore
                }
            }
        };
    }, [clearAutoStopTimer]);

        return {
        state,
        transcript,
        error,
        mediaStream,
        startRecording,
        stopRecording,
        cancelRecording,
        reset,
        isRecording: state === 'recording',
        isProcessing: state === 'processing',
        hasError: state === 'error',
    };
}
