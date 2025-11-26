# Frontend Setup Guide

This guide explains the Next.js frontend setup for UNJobAtlas, including the architecture, components, and how Django serves the static frontend.

## Overview

The frontend is a **Next.js 16** single-page application built with:
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: High-quality React component library
- **Static Export**: Compiled to static HTML/CSS/JS served by Django

## Architecture

### Static File Serving

The frontend is built as a static export and served directly by Django:

1. **Build Process**: Next.js compiles to static files in `frontend/build/`
2. **Django Configuration**: Serves static assets and `index.html` template
3. **Single Process**: No separate Node.js server needed in production or development

### Three-Column Layout

The application uses a fixed desktop-only layout (no responsive design needed):

```
┌────────────────────────────────────────────────────────┐
│  Search Filters │   Job List   │    Job Details        │
│     (280px)     │   (flex-1)   │      (600px)          │
│                 │              │                        │
│  Organization   │  Job Card 1  │  Selected Job Info    │
│  Location       │  Job Card 2  │  - Title              │
│  Contract Type  │  Job Card 3  │  - Organization       │
│  Languages      │  Job Card 4  │  - Location           │
│  Position Level │     ...      │  - Description        │
│                 │              │  - Requirements       │
│                 │              │  - Languages          │
└────────────────────────────────────────────────────────┘
```

## Directory Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with metadata
│   ├── page.tsx            # Main page with three-column layout
│   └── globals.css         # Global styles and Tailwind imports
├── components/
│   ├── ui/                 # shadcn/ui components
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── checkbox.tsx
│   │   ├── select.tsx
│   │   ├── scroll-area.tsx
│   │   └── separator.tsx
│   ├── SearchFilters.tsx   # Left column: faceted search filters
│   ├── JobList.tsx         # Center column: scrollable job list
│   └── JobDetails.tsx      # Right column: selected job details
├── lib/
│   └── utils.ts            # Utility functions (cn helper)
├── build/                  # Built static files (gitignored)
├── next.config.ts          # Next.js configuration
├── tailwind.config.ts      # Tailwind CSS configuration
├── components.json         # shadcn/ui configuration
└── package.json            # Dependencies and scripts
```

## Components

### SearchFilters Component (Left Column)

**Location**: `frontend/components/SearchFilters.tsx`

Features:
- Organization filter (select dropdown)
- Location filter (country input)
- Contract type (checkboxes)
- Languages (checkboxes)
- Position level (checkboxes)
- Clear filters button

Currently uses mock data. Will connect to Django API endpoint `/api/facets/` for:
- Available organizations
- Countries with job counts
- Contract type counts
- Language counts
- Position level counts

### JobList Component (Center Column)

**Location**: `frontend/components/JobList.tsx`

Features:
- Scrollable list of job cards
- Click to select and view details
- Displays: post number, title, organization, location, deadline
- Badge indicators for contract type, work arrangement
- Visual highlight for selected job

Currently uses mock data. Will connect to Django API endpoint `/api/jobs/` with query parameters for filtering and pagination.

### JobDetails Component (Right Column)

**Location**: `frontend/components/JobDetails.tsx`

Features:
- Complete job information display
- Sections: Basic Info, Description, Requirements, Languages, Additional Info
- Badges for contract type, work arrangement, position level
- Formatted dates and currency
- Language requirements with proficiency levels
- External link to original posting

Shows placeholder when no job is selected. Data passed from parent via props.

### Main Page (Layout Orchestration)

**Location**: `frontend/app/page.tsx`

Responsibilities:
- State management (selected job, filters)
- Three-column layout coordination
- Props passing to child components
- Currently manages mock data (will add API calls)

## Installation & Setup

### Prerequisites

- Node.js 18+ and npm
- Django project already set up

### Initial Setup

The frontend is already initialized, but if you need to recreate or modify:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server (for frontend-only development)
npm run dev

# Build for production
npm run build
```

### Development Workflow

#### Option 1: Integrated (Recommended)

Run Django server which serves the built frontend:

```bash
# Build frontend
cd frontend && npm run build && cd ..

# Start Django
python manage.py runserver

# Visit http://127.0.0.1:8000/
```

#### Option 2: Separate (Frontend Development)

For rapid frontend iteration with hot reload:

```bash
# Terminal 1: Django API server
python manage.py runserver

# Terminal 2: Next.js dev server
cd frontend && npm run dev

# Visit http://localhost:3000/
# API calls will go to Django at http://127.0.0.1:8000/
```

**Note**: When using separate servers, ensure CORS is configured in Django settings (already done).

## Configuration

### Next.js Configuration

File: `frontend/next.config.ts`

```typescript
const nextConfig: NextConfig = {
  output: 'export',        // Static export for Django serving
  distDir: 'build',        // Output directory
  images: {
    unoptimized: true,     // Required for static export
  },
};
```

### Django Configuration

**Settings** (`config/settings.py`):

```python
# Template directory for index.html
TEMPLATES[0]['DIRS'] = [BASE_DIR / "frontend" / "build"]

# Static files from Next.js build
STATICFILES_DIRS = [
    BASE_DIR / "frontend" / "build",
]
```

**URLs** (`config/urls.py`):

```python
# Serve Next.js frontend at root
path("", TemplateView.as_view(template_name="index.html"), name="home"),

# In development, serve static files
if settings.DEBUG:
    from django.contrib.staticfiles.views import serve
    urlpatterns += [re_path(r'^(?P<path>.*)$', serve)]
```

## Building for Production

### 1. Build Frontend

```bash
cd frontend
npm run build
cd ..
```

This creates optimized static files in `frontend/build/`:
- `index.html` - Main HTML file
- `_next/static/` - JavaScript, CSS, and other assets
- Any files in `public/` directory

### 2. Collect Static Files (Production)

For production deployment with WhiteNoise or similar:

```bash
python manage.py collectstatic --noinput
```

This copies all static files to `STATIC_ROOT` for serving.

### 3. Deploy

Deploy as a standard Django application. The frontend is just static files served by Django.

## API Integration

### Current State: Mock Data

All components currently use hardcoded mock data defined in each component file.

### Next Steps: Connect to Django API

#### 1. Create Django REST API Endpoints

**Required endpoints**:

```
GET /api/jobs/                    # List jobs with filtering
GET /api/jobs/:id/                # Job detail
GET /api/facets/                  # Filter options with counts
```

**Example**: Create `core/serializers.py` and update `core/views.py`:

```python
# core/serializers.py
from rest_framework import serializers
from .models import JobAdvertisement

class JobAdvertisementSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAdvertisement
        fields = '__all__'

# core/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .documents import JobAdvertisementDocument

@api_view(['GET'])
def job_list(request):
    # Use Elasticsearch for filtering
    search = JobAdvertisementDocument.search()
    
    # Apply filters from query params
    if org := request.GET.get('organization'):
        search = search.filter('term', organization_name__keyword=org)
    
    # Execute and serialize
    results = search.execute()
    # ... serialize and return
```

#### 2. Update Frontend to Call API

**In `app/page.tsx`**:

```typescript
// Replace mock data with API calls
const [jobs, setJobs] = useState<Job[]>([]);
const [loading, setLoading] = useState(false);

useEffect(() => {
  const fetchJobs = async () => {
    setLoading(true);
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/jobs/?${params}`);
    const data = await response.json();
    setJobs(data.results);
    setLoading(false);
  };
  
  fetchJobs();
}, [filters]);
```

#### 3. Add Pagination

Implement cursor or page-based pagination in both API and frontend.

#### 4. Add Loading States

Use Skeleton components from shadcn/ui for loading indicators.

## Customization

### Adding New UI Components

```bash
cd frontend

# Browse available components at https://ui.shadcn.com/
npx shadcn add [component-name]

# Example: Add a dialog component
npx shadcn add dialog
```

Components are installed to `frontend/components/ui/`.

### Styling

Tailwind CSS classes are used throughout. Global styles in `frontend/app/globals.css`.

To modify theme colors, edit `frontend/tailwind.config.ts`:

```typescript
theme: {
  extend: {
    colors: {
      // Customize theme colors
    },
  },
},
```

### Adding New Pages

With static export, all pages must be defined at build time:

```bash
# Create a new route
mkdir -p frontend/app/about
touch frontend/app/about/page.tsx
```

Then rebuild the frontend.

## Troubleshooting

### Frontend Not Loading

1. **Check build exists**:
   ```bash
   ls -la frontend/build/index.html
   ```

2. **Rebuild frontend**:
   ```bash
   cd frontend && npm run build
   ```

3. **Check Django settings**:
   - `TEMPLATES[0]['DIRS']` includes `frontend/build`
   - `STATICFILES_DIRS` includes `frontend/build`

4. **Check URL configuration**:
   - Root URL serves `TemplateView` with `index.html`
   - Static file serving enabled in development

### Static Assets Not Loading

1. **Verify DEBUG mode**:
   ```python
   # In settings.py
   DEBUG = True  # Required for development static serving
   ```

2. **Check URL patterns**:
   ```python
   # In urls.py
   if settings.DEBUG:
       from django.contrib.staticfiles.views import serve
       urlpatterns += [re_path(r'^(?P<path>.*)$', serve)]
   ```

3. **Check browser console**: Look for 404 errors on `_next/static/*` files

### TypeScript Errors

```bash
cd frontend

# Check for type errors
npm run build

# Fix common issues
npm install --save-dev @types/react @types/node
```

### CORS Issues (Separate Dev Servers)

If running frontend on port 3000 and Django on port 8000:

1. **Verify CORS settings** in `config/settings.py`:
   ```python
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:3000",
       "http://127.0.0.1:3000",
   ]
   ```

2. **Check corsheaders middleware** is installed and enabled

## Next Steps

1. **Implement Django REST API**:
   - Install `djangorestframework`
   - Create serializers for `JobAdvertisement`
   - Implement `/api/jobs/`, `/api/jobs/:id/`, `/api/facets/` endpoints
   - Use Elasticsearch for search and filtering

2. **Connect Frontend to API**:
   - Replace mock data with `fetch()` calls
   - Add loading states and error handling
   - Implement real-time filtering
   - Add pagination

3. **Enhance Features**:
   - URL state management (filters in query params)
   - Bookmark/save jobs functionality
   - Export job list to CSV
   - Advanced search (full-text, date ranges)

4. **Optimize**:
   - Add request caching
   - Implement infinite scroll or pagination
   - Add analytics tracking
   - Set up CI/CD for automatic frontend builds

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Django Static Files](https://docs.djangoproject.com/en/4.2/howto/static-files/)
