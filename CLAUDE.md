# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Project Overview

EditEase is an AI-assisted video editing platform that processes raw footage using AI to detect scenes and analyze emotions, providing reviewers with a visual clip-grid workspace.

## Key Directories

- `api/` - Main API and backend logic
- `frontend/` - React-based UI
- `pipeline/` - Video processing and AI analysis logic
- `services/` - Business logic for various features
- `tests/` - Test files

## Key Commands

- `make install` - Install dependencies
- `make run-api` - Run the API server
- `make run-frontend` - Run the frontend development server
- `make run-celery` - Start the Celery worker for background tasks
- `make run-pipeline` - Run the video processing pipeline

## Development Tools

The project uses several development tools:
- Python 3.9+
- Node.js 16+
- FFmpeg for video processing
- MongoDB for database
- Redis for caching and session storage
- Celery for background task processing

## Testing

- `pytest tests/` - Run all tests
- Run individual test: `pytest tests/test_api.py`

## High-level Architecture

The system is divided into three main components:
1. API (Flask-based server)
2. Video Processing Pipeline (uses OpenCV, scene detection)
3. Frontend (React-based UI)

## Code Structure

The codebase is organized into the following main layers:
- Frontend (React with Vite)
- Backend API (Flask)
- Video Processing Pipeline (Python-based)
- Services (Python-based)
- UI (Streamlit-based admin interface)

## Design System

The project includes a comprehensive design system with:
- GitHub-Dark inspired palette
- Glass workspace panels
- Consistent typography (Inter + JetBrains Mono)
- Standardized components and UI patterns
- Lucide React icons
- Specific color and spacing guidelines

## Brand Voice

The brand voice is confident and focused on removing tedium from video editing:
- "Stop sorting footage manually"
- Clear, kinetic, second person copy
- Crisp imperatives over fluff
- Technical and concrete descriptions

## Frontend Development

The frontend is built with React 19, Vite, and React Router, with:
- GSAP + Lenis for scroll/animation
- Recharts for data visualization
- Lucide React for icons
- react-joyride for tours
- Specific component and styling guidelines

## API Development

The API is built with Flask and includes:
- User authentication and authorization
- Video processing and management
- Cloudinary integration for video storage
- Email service integration
- Task management
- Service layer for business logic

## Video Processing

The video processing pipeline includes:
- OpenCV for video analysis
- Scene detection algorithms
- Emotion analysis
- Automated video organization
- Batch processing capabilities

## Deployment

The project can be deployed using:
- Docker (recommended)
- Standard Python deployment
- Cloud hosting platforms (AWS, GCP, Azure)
- CDN for static assets
- Database migrations and seeding