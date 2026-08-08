# AI Healthcare System

An AI-powered healthcare application for medicine discovery, nearby healthcare services, prescription handling, reminders, feedback, and emergency support.

## Features

- AI health assistant for medicine and symptom queries
- Medicine search and medicine details
- Generic alternatives and medicine comparisons
- Nearby hospitals, pharmacies, clinics, labs, and blood banks
- Prescription scanning and report storage
- Medicine reminders and health tracking
- Customer feedback and ratings
- Emergency SOS support

## App Sections

- **Home**: AI assistant, reminders, health summary, emergency shortcuts
- **Store**: medicine search, details, alternatives, reviews, ordering
- **Maps**: nearby hospitals, medical stores, clinics, labs, blood banks
- **Profile**: personal details, medical history, settings, contacts

## Architecture

- **Frontend**: Flutter mobile app
- **Backend**: FastAPI / Python
- **Database**: PostgreSQL or Firebase
- **AI Services**: Gemini / OpenAI
- **Maps**: Google Maps API
- **Notifications**: Firebase Cloud Messaging
- **Storage**: Firebase Storage / AWS S3

## Main Workflow

1. User opens the app and signs in.
2. User searches for medicine or asks the AI assistant.
3. Backend fetches medicine details, alternatives, and store availability.
4. Maps module shows nearby healthcare locations.
5. User can save records, receive reminders, and send feedback.

## Project Structure

```text
ai_healthcare_system/
├── lib/
├── assets/
├── android/
├── ios/
├── backend/
├── datasets/
└── README.md
