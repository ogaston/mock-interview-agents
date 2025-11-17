# Web Frontend - Mock Interview Agents

A modern, AI-powered interview coaching platform built with Next.js and React.

## Overview

Mock Interview Agents is an interactive web application designed to help users practice technical and behavioral interviews. The platform provides personalized feedback, tracks progress, and offers recommendations for improvement.

## Features

### 🎯 Interview Setup
- Select from multiple role types (Frontend, Backend, Full Stack, Product Manager, Data Scientist)
- Choose experience level (Junior, Mid-level, Senior)
- Clean, intuitive setup interface

### 💬 Interview Session
- Step-by-step question flow with progress tracking
- Text-based answer submission
- Navigation between questions
- Real-time progress indicators

### 📊 Feedback & Analytics
- Comprehensive performance scoring across multiple dimensions:
  - Clarity
  - Confidence
  - Relevance
  - Communication
- Visual score breakdowns with progress bars
- Personalized improvement recommendations
- Overall performance summary

### 📚 Session History
- View past interview sessions
- Track progress over time
- Quick access to previous feedback

## Technology Stack

### Core
- **Next.js 16** - React framework with App Router
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Styling

### UI Components
- **shadcn/ui** - Component library (New York style)
- **Radix UI** - Accessible component primitives
- **Lucide React** - Icon library

### Additional Libraries
- **React Hook Form** - Form management
- **Zod** - Schema validation
- **date-fns** - Date utilities
- **next-themes** - Theme management
- **Vercel Analytics** - Analytics integration

## Project Structure

```
web/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main page (view router)
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── interview-setup.tsx      # Interview configuration
│   ├── interview-session.tsx    # Interview flow
│   ├── feedback-view.tsx        # Results display
│   ├── session-history.tsx      # History view
│   └── ui/               # shadcn/ui components
├── hooks/                # Custom React hooks
├── lib/                  # Utilities
│   └── utils.ts         # Helper functions
└── public/               # Static assets
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- pnpm (recommended) or npm/yarn

### Installation

1. Navigate to the web directory:
```bash
cd web
```

2. Install dependencies:
```bash
pnpm install
```

3. Run the development server:
```bash
pnpm dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint

## Application Flow

1. **Setup** → User selects role and experience level
2. **Session** → User answers interview questions sequentially
3. **Feedback** → System provides scores and recommendations
4. **History** → User can review past sessions

## Current State

The application currently uses mock data for:
- Interview questions (hardcoded set)
- Answer evaluation (simulated with delays)
- Feedback generation (static scores and suggestions)

Future integration with backend services will replace these mock implementations.

## Styling

The application uses:
- Tailwind CSS for utility-first styling
- CSS variables for theming
- shadcn/ui components for consistent design
- Responsive design patterns

## Development Notes

- All components are client-side (`'use client'`)
- State management is handled with React hooks
- No backend integration yet (mock data in use)
- Session history is stored in component state (not persisted)

## Future Enhancements

- Backend API integration
- User authentication
- Persistent session storage
- Real-time AI evaluation
- Custom question sets
- Video/audio interview support
- Advanced analytics dashboard

