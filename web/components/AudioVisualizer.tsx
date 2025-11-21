'use client';

import { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

interface AudioVisualizerProps {
    isActive: boolean;
    mode: 'speaking' | 'listening' | 'thinking'; // Added 'thinking' mode
    stream?: MediaStream | null;
    audioElement?: HTMLAudioElement | null;
    className?: string;
}

export function AudioVisualizer({ 
    isActive, 
    mode, 
    stream, 
    audioElement,
    className 
}: AudioVisualizerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number>();
    const analyserRef = useRef<AnalyserNode>();
    const audioContextRef = useRef<AudioContext>();
    const sourceRef = useRef<MediaStreamAudioSourceNode | MediaElementAudioSourceNode>();

    useEffect(() => {
        // If not active, clear canvas and return
        if (!isActive) {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
            const canvas = canvasRef.current;
            const ctx = canvas?.getContext('2d');
            if (canvas && ctx) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                if (mode === 'thinking') {
                     // Thinking animation (gentle pulsing) handled in render loop
                     // But if inactive & thinking, we should still animate? 
                     // 'isActive' should be true for thinking.
                } else {
                    // Optional: Draw a faint idle state instead of full dots
                    // Just a single horizontal line or smaller dots
                    const centerY = canvas.height / 2;
                    ctx.fillStyle = mode === 'listening' ? '#ef4444' : '#0ea5e9';
                    ctx.globalAlpha = 0.2; // Faint
                    
                    // Draw 3 subtle dots
                    for (let i = 0; i < 3; i++) {
                        const x = (canvas.width / 2) + (i - 1) * 15;
                        ctx.beginPath();
                        ctx.arc(x, centerY, 1.5, 0, Math.PI * 2);
                        ctx.fill();
                    }
                    ctx.globalAlpha = 1.0;
                }
            }
            return;
        }

        // Initialize Audio Context
        if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        }
        const ctx = audioContextRef.current;
        if (ctx.state === 'suspended') {
            ctx.resume();
        }

        // Initialize Analyser
        if (!analyserRef.current) {
            analyserRef.current = ctx.createAnalyser();
            analyserRef.current.fftSize = 64; // Small FFT for fewer bins
            analyserRef.current.smoothingTimeConstant = 0.85; // High smoothing for less jitter
            analyserRef.current.minDecibels = -90;
            analyserRef.current.maxDecibels = -10;
        }
        const analyser = analyserRef.current;

        // Setup Source
        try {
            if (mode === 'listening' && stream) {
                if (sourceRef.current) sourceRef.current.disconnect();
                sourceRef.current = ctx.createMediaStreamSource(stream);
                sourceRef.current.connect(analyser);
            } else {
                // Speaking or no stream: we will simulate visualization in the render loop
                // No source needed connected to analyser
            }
        } catch (e) {
            console.error('Audio source setup failed', e);
        }

        // Animation Loop
        const render = () => {
            const canvas = canvasRef.current;
            const canvasCtx = canvas?.getContext('2d');
            if (!canvas || !canvasCtx) return;

            canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            const numBars = 5;
            const barWidth = 6; // Fixed width for aesthetics
            const gap = 6;
            const totalWidth = (numBars * barWidth) + ((numBars - 1) * gap);
            const startX = (canvas.width - totalWidth) / 2;
            const centerY = canvas.height / 2;

            let values: number[] = [];

            if (mode === 'listening' && stream) {
                analyser.getByteFrequencyData(dataArray);
                
                // Map frequency data to our 5 bars
                // We grab a few distinct ranges
                const step = Math.floor(bufferLength / numBars);
                for (let i = 0; i < numBars; i++) {
                    let sum = 0;
                    for(let j=0; j<step; j++) {
                        sum += dataArray[i*step + j];
                    }
                    values.push(sum / step);
                }
            } else if (mode === 'thinking') {
                 // Thinking animation: Loading wave
                 const time = Date.now() / 200;
                 for (let i = 0; i < numBars; i++) {
                    // Traveling wave effect
                    const offset = i * 1.0;
                    const value = (Math.sin(time + offset) + 1) * 0.5 * 150 + 50;
                    values.push(value);
                 }
            } else {
                // Simulate smooth organic movement for AI speaking
                // Slower time factor (was 150)
                const time = Date.now() / 200; 
                for (let i = 0; i < numBars; i++) {
                     // Perlin-ish noise using sine waves
                     // Reduced amplitude constants
                     const value = Math.abs(Math.sin(time + i * 0.5) * 100) + 
                                   Math.abs(Math.cos(time * 0.5 + i) * 40);
                     values.push(Math.min(255, value));
                }
            }

            // Draw Bars
            values.forEach((value, i) => {
                // Normalize height (0-255 -> 4px to max height)
                // Apply extra dampening for smoother look
                const normalizedHeight = Math.max(4, (value / 255) * (canvas.height * 0.8));
                
                const x = startX + (i * (barWidth + gap));
                const y = centerY - (normalizedHeight / 2);

                if (mode === 'listening') {
                    canvasCtx.fillStyle = '#ef4444';
                } else if (mode === 'thinking') {
                    canvasCtx.fillStyle = '#f59e0b'; // Amber/Orange for thinking
                } else {
                    canvasCtx.fillStyle = '#0ea5e9';
                }
                
                canvasCtx.beginPath();
                // Use roundRect if available, else rect
                if (canvasCtx.roundRect) {
                    canvasCtx.roundRect(x, y, barWidth, normalizedHeight, 10);
                } else {
                    canvasCtx.rect(x, y, barWidth, normalizedHeight);
                }
                canvasCtx.fill();
            });

            animationRef.current = requestAnimationFrame(render);
        };

        render();

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
            // Do not close AudioContext as it's expensive, but disconnect source
            if (sourceRef.current) {
                sourceRef.current.disconnect();
            }
        };

    }, [isActive, mode, stream, audioElement]);

    return (
        <canvas 
            ref={canvasRef} 
            width={120} 
            height={40} 
            className={cn("block mx-auto", className)}
        />
    );
}
