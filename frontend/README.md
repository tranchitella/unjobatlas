# UN Job Atlas Frontend

A modern Next.js application for searching and exploring UN job opportunities.

## Tech Stack

- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **API**: Django REST backend

## Features

- **Three-Column Layout**:
  - Left: Faceted search filters
  - Center: Job listings
  - Right: Detailed job view

- **Real-time Filtering**: All filters update dynamically
- **Elasticsearch Integration**: Fast, powerful search
- **Desktop Optimized**: Built for desktop use

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Django backend running on `http://localhost:8000`

### Development

```bash
# Install dependencies
npm install

# Start the development server
npm run dev

# Or use the helper script from project root
./scripts/run_frontend.sh
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main page (three-column layout)
│   └── globals.css         # Global styles
├── components/
│   ├── ui/                 # shadcn/ui components
│   ├── SearchFilters.tsx   # Left column - filters
│   ├── JobList.tsx         # Center column - job listings
│   └── JobDetails.tsx      # Right column - job details
└── lib/
    └── utils.ts            # Utility functions
```

## Components Overview

### SearchFilters (Left Column)
- Text search input
- Active jobs toggle
- Faceted filters: Organizations, Countries, Contract Types, Position Levels, Work Arrangements

### JobList (Center Column)
- Job cards with key information
- Click to view details in right column

### JobDetails (Right Column)
- Complete job information
- Skills, qualifications, requirements
- Language requirements
- Apply button

## API Integration

Configure the Django backend URL:

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

CORS is configured in Django for `localhost:3000`.

## Mock Data

Currently uses mock data. Once Django API endpoints are ready, update:
- `components/JobList.tsx`
- `components/JobDetails.tsx`
- `components/SearchFilters.tsx`

## Next Steps

1. Create Django API endpoints (`/api/jobs/`, `/api/jobs/:id/`, `/api/facets/`)
2. Implement API client in `lib/api.ts`
3. Replace mock data with real API calls
4. Add pagination and URL state management

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Tailwind CSS](https://tailwindcss.com/docs)
