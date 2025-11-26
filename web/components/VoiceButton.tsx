/**
 * VoiceButton - Animated microphone button for voice recording
 */
'use client';

import React from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface VoiceButtonProps {
    isRecording: boolean;
    isProcessing: boolean;
    hasError: boolean;
    onStart: () => void;
    onStop: () => void;
    onStopAndSubmit?: () => void; // Called when recording stops (for auto-submit)
    supportPressAndHold?: boolean; // Enable press-and-hold mode (default: true)
    className?: string;
    disabled?: boolean;
}

export function VoiceButton({
    isRecording,
    isProcessing,
    hasError,
    onStart,
    onStop,
    onStopAndSubmit,
    supportPressAndHold = true,
    className,
    disabled = false,
}: VoiceButtonProps) {
    const [isPressHoldActive, setIsPressHoldActive] = React.useState(false);
    const pressHoldTimerRef = React.useRef<NodeJS.Timeout | null>(null);

    // Handle click-to-toggle mode
    const handleClick = () => {
        // Ignore click if it was a press-and-hold gesture
        if (isPressHoldActive) {
            setIsPressHoldActive(false);
            return;
        }

        if (isRecording) {
            // Stop and submit when clicking while recording
            onStop();
            if (onStopAndSubmit) {
                // Small delay to ensure recording stops first
                setTimeout(() => onStopAndSubmit(), 100);
            }
        } else {
            onStart();
        }
    };

    // Handle press-and-hold mode
    const handlePressStart = (e: React.MouseEvent | React.TouchEvent) => {
        if (!supportPressAndHold || disabled || isProcessing) return;

        // Set a timer to detect if this is a press-and-hold (not just a click)
        pressHoldTimerRef.current = setTimeout(() => {
            setIsPressHoldActive(true);
        }, 150); // 150ms threshold to distinguish press-hold from click

        if (!isRecording) {
            onStart();
        }
    };

    const handlePressEnd = (e: React.MouseEvent | React.TouchEvent) => {
        if (!supportPressAndHold) return;

        // Clear the timer
        if (pressHoldTimerRef.current) {
            clearTimeout(pressHoldTimerRef.current);
            pressHoldTimerRef.current = null;
        }

        // If press-hold was active and we're recording, stop and submit
        if (isPressHoldActive && isRecording) {
            onStop();
            if (onStopAndSubmit) {
                // Small delay to ensure recording stops first
                setTimeout(() => onStopAndSubmit(), 100);
            }
            setIsPressHoldActive(false);
        }
    };

    // Cleanup timer on unmount
    React.useEffect(() => {
        return () => {
            if (pressHoldTimerRef.current) {
                clearTimeout(pressHoldTimerRef.current);
            }
        };
    }, []);

    return (
        <button
            onClick={handleClick}
            onMouseDown={handlePressStart}
            onMouseUp={handlePressEnd}
            onMouseLeave={handlePressEnd}
            onTouchStart={handlePressStart}
            onTouchEnd={handlePressEnd}
            disabled={disabled || isProcessing}
            className={cn(
                'relative flex items-center justify-center rounded-full transition-all duration-200',
                'w-12 h-12 md:w-14 md:h-14',
                'focus:outline-none focus:ring-2 focus:ring-offset-2',
                isRecording && 'bg-red-500 hover:bg-red-600 focus:ring-red-500',
                !isRecording && !hasError && 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-500',
                hasError && 'bg-gray-400',
                isProcessing && 'opacity-75 cursor-not-allowed',
                disabled && 'opacity-50 cursor-not-allowed',
                className
            )}
            aria-label={isRecording ? 'Detener grabación' : 'Iniciar grabación'}
        >
            {/* Pulsing animation when recording */}
            {isRecording && (
                <>
                    <span className="absolute inset-0 animate-ping bg-red-400 rounded-full opacity-75" />
                    <span className="absolute inset-0 animate-pulse bg-red-300 rounded-full opacity-50" />
                </>
            )}

            {/* Icon */}
            <span className="relative z-10 text-white flex items-center justify-center w-full h-full">
                {isProcessing ? (
                    <Loader2 className="w-[40%] h-[40%] animate-spin" />
                ) : isRecording ? (
                    <MicOff className="w-[40%] h-[40%]" />
                ) : (
                    <Mic className="w-[40%] h-[40%]" />
                )}
            </span>

            {/* Recording indicator */}
            {isRecording && (
                <span className="absolute -bottom-1 -right-1 w-3 h-3 bg-red-600 rounded-full border-2 border-white" />
            )}
        </button>
    );
}

/**
 * VoiceButtonWithHint - VoiceButton with helpful text hint
 */
export function VoiceButtonWithHint(props: VoiceButtonProps) {
    const { isRecording, isProcessing } = props;

    return (
        <div className="flex flex-col items-center gap-2">
            <VoiceButton {...props} />
            <p className="text-xs text-gray-500 dark:text-gray-400">
                {isProcessing
                    ? 'Procesando...'
                    : isRecording
                        ? 'Clic para detener'
                        : 'Clic para hablar'}
            </p>
        </div>
    );
}
