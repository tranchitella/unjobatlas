# Elasticsearch Integration

## Overview

This document describes the Elasticsearch integration for the UN Job Atlas project. Elasticsearch provides powerful full-text search, filtering, and aggregation capabilities for job advertisements.

## Architecture

### Components

1. **Elasticsearch Service**: Running in Docker, stores and indexes job advertisements
2. **Django-Elasticsearch-DSL**: Django integration library that handles indexing and querying
3. **JobAdvertisementDocument**: Defines the Elasticsearch document structure and mappings
4. **Real-time Indexing**: Automatic indexing via Django signals

### Data Flow

```
JobAdvertisement Created/Updated
    ↓
Django Signal (post_save)
    ↓
RealTimeSignalProcessor
    ↓
Elasticsearch Index Updated
```

## Setup

### 1. Docker Compose Configuration

Elasticsearch is configured in `docker-compose.yml`:

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.19.7
  container_name: unjobatlas_elasticsearch
  restart: unless-stopped
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
  ports:
    - "9200:9200"
    - "9300:9300"
  volumes:
    - ./elasticsearch_data:/usr/share/elasticsearch/data
```

**Key Settings:**
- **Single-node mode**: Suitable for development
- **Security disabled**: Simplifies local development (enable in production!)
- **Memory limit**: 512MB heap size (adjust based on data volume)
- **Ports**: 9200 (HTTP API), 9300 (Transport)

### 2. Environment Variables

Add to your `.env` file:

```bash
ELASTICSEARCH_DSL_HOSTS=http://localhost:9200
ELASTICSEARCH_DSL_AUTOSYNC=True
```

### 3. Django Settings

Configuration in `config/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    "django_elasticsearch_dsl",
    # ...
]

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": config("ELASTICSEARCH_DSL_HOSTS", default="http://localhost:9200")
    },
}

ELASTICSEARCH_DSL_AUTOSYNC = config(
    "ELASTICSEARCH_DSL_AUTOSYNC", default=True, cast=bool
)

ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = (
    "django_elasticsearch_dsl.signals.RealTimeSignalProcessor"
)
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Added packages:
- `django-elasticsearch-dsl>=8.0`
- `elasticsearch>=8.19.7,<9.0.0`

### 5. Start Services

```bash
docker-compose up -d
```

Wait for Elasticsearch to be healthy:

```bash
curl http://localhost:9200/_cluster/health
```

### 6. Create and Populate Index

```bash
# Create the index structure
python manage.py search_index --create

# Populate with existing data
python manage.py rebuild_index
```

Or use the custom rebuild command with delete option:

```bash
python manage.py rebuild_index --delete
```

## Document Structure

### JobAdvertisementDocument

Defined in `core/documents.py`, this document includes:

#### Fields

**Basic Information:**
- `post_number` (text + keyword)
- `post_name` (text with english analyzer + keyword + suggestions)
- `date_posted` (date)
- `application_deadline` (date)

**Organization (nested object):**
- `organization.id` (integer)
- `organization.name` (text + keyword + suggestions)
- `organization.abbreviation` (text + keyword + suggestions)

**Contract Details:**
- `contract_type` (keyword)
- `contract_duration` (text)
- `renewable` (boolean)

**Location (with suggestions):**
- `location_region` (text + keyword + suggestions)
- `location_country` (text + keyword + suggestions)
- `location_city` (text + keyword + suggestions)
- `work_arrangement` (keyword)

**Position:**
- `thematic_area` (text + keyword)
- `position_level` (keyword)

**Requirements (full-text search):**
- `brief_description` (text, english analyzer)
- `main_skills_competencies` (text, english analyzer)
- `technical_skills` (text, english analyzer)
- `minimum_academic_qualifications` (text, english analyzer)
- `minimum_experience` (text, english analyzer)

**Language Requirements (nested):**
- `language_requirements.language` (text + keyword)
- `language_requirements.requirement_level` (keyword)
- `language_requirements.proficiency_level` (keyword)

**Metadata:**
- `tags` (keyword array)
- `source_url` (keyword)
- `created_at` (date)
- `updated_at` (date)
- `is_active` (boolean, computed)
- `days_until_deadline` (integer, computed)

### Indexing Strategy

**Multi-field Mapping:**
- Text fields have both `text` (for full-text search) and `keyword` (for exact match/aggregations)
- Key fields include `suggest` completion field for autocomplete

**Analyzers:**
- English analyzer for job descriptions and requirements
- Standard analyzer for most text fields
- Keyword analyzer for exact matches

**Nested Objects:**
- Language requirements stored as nested documents for complex queries

## Usage Examples

### Searching from Django

```python
from core.documents import JobAdvertisementDocument
from elasticsearch_dsl import Q

# Simple search
search = JobAdvertisementDocument.search()
results = search.query("match", post_name="Programme Officer")

# Multi-field search
search = JobAdvertisementDocument.search()
query = Q("multi_match", query="emergency response", fields=[
    "post_name",
    "brief_description",
    "main_skills_competencies"
])
results = search.query(query)

# Filter by location
search = JobAdvertisementDocument.search()
results = search.filter("term", location_country__keyword="Kenya")

# Active jobs only
from datetime import date
search = JobAdvertisementDocument.search()
results = search.filter("range", application_deadline={"gte": date.today()})

# Filter by organization
search = JobAdvertisementDocument.search()
results = search.filter("term", organization__name__keyword="UNICEF")

# Combine filters and search
search = JobAdvertisementDocument.search()
search = search.query("match", brief_description="child protection")
search = search.filter("term", contract_type="fixed_term")
search = search.filter("term", location_country__keyword="Thailand")
results = search.execute()

# Pagination
search = JobAdvertisementDocument.search()[0:20]  # First 20 results

# Sorting
search = JobAdvertisementDocument.search()
search = search.sort("-date_posted")  # Newest first

# Aggregations
search = JobAdvertisementDocument.search()
search.aggs.bucket("by_country", "terms", field="location_country.keyword")
search.aggs.bucket("by_organization", "terms", field="organization.name.keyword")
results = search.execute()

# Access aggregations
for bucket in results.aggregations.by_country.buckets:
    print(f"{bucket.key}: {bucket.doc_count}")
```

### Autocomplete/Suggestions

```python
from elasticsearch_dsl import Search

# Organization name suggestions
s = Search(index="job_advertisements")
s = s.suggest("org_suggest", "unic", completion={"field": "organization.name.suggest"})
response = s.execute()

for option in response.suggest.org_suggest[0].options:
    print(option.text)
```

### Complex Queries

```python
from elasticsearch_dsl import Q

# Boolean query: (UNICEF OR WFP) AND (Kenya OR Uganda) AND active
search = JobAdvertisementDocument.search()

org_query = Q("terms", organization__name__keyword=["UNICEF", "WFP"])
location_query = Q("terms", location_country__keyword=["Kenya", "Uganda"])
active_query = Q("range", application_deadline={"gte": date.today()})

search = search.query(Q("bool", must=[org_query, location_query, active_query]))
results = search.execute()

# Nested query for language requirements
search = JobAdvertisementDocument.search()
nested_query = Q(
    "nested",
    path="language_requirements",
    query=Q("bool", must=[
        Q("term", language_requirements__language__keyword="French"),
        Q("term", language_requirements__requirement_level="required")
    ])
)
results = search.query(nested_query)
```

## Management Commands

### search_index

Django-elasticsearch-dsl provides several management commands:

```bash
# Create indices
python manage.py search_index --create

# Rebuild indices (delete and create)
python manage.py search_index --rebuild

# Populate indices
python manage.py search_index --populate

# Delete indices
python manage.py search_index --delete
```

### rebuild_index (Custom)

Custom command in `core/management/commands/rebuild_index.py`:

```bash
# Rebuild index (create if not exists)
python manage.py rebuild_index

# Delete existing index first
python manage.py rebuild_index --delete
```

Features:
- Progress tracking (reports every 100 records)
- Optional index deletion
- Uses optimized queryset with select_related/prefetch_related

## Real-time Indexing

Indexing happens automatically via `RealTimeSignalProcessor`:

1. **JobAdvertisement created/updated** → Indexed immediately
2. **Organization updated** → All related JobAdvertisements re-indexed
3. **LanguageRequirement added/changed** → Related JobAdvertisement re-indexed

### Disable Auto-sync (Optional)

For bulk operations, temporarily disable:

```python
from django.conf import settings

# Temporarily disable
settings.ELASTICSEARCH_DSL_AUTOSYNC = False

# Perform bulk operations
JobAdvertisement.objects.bulk_create([...])

# Re-enable
settings.ELASTICSEARCH_DSL_AUTOSYNC = True

# Rebuild index
from core.documents import JobAdvertisementDocument
doc = JobAdvertisementDocument()
for instance in JobAdvertisement.objects.all():
    doc.update(instance)
```

## Monitoring

### Check Cluster Health

```bash
curl http://localhost:9200/_cluster/health?pretty
```

### Check Index Status

```bash
curl http://localhost:9200/_cat/indices?v
```

### Count Documents

```bash
curl http://localhost:9200/job_advertisements/_count?pretty
```

### View Index Mapping

```bash
curl http://localhost:9200/job_advertisements/_mapping?pretty
```

### Search Examples via REST API

```bash
# Simple match query
curl -X GET "http://localhost:9200/job_advertisements/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "post_name": "Programme Officer"
    }
  }
}
'

# Filter by country
curl -X GET "http://localhost:9200/job_advertisements/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "location_country.keyword": "Kenya"
    }
  }
}
'
```

## Performance Optimization

### Index Settings

Current settings in `JobAdvertisementDocument.Index`:

```python
settings = {
    "number_of_shards": 1,      # Single shard for small dataset
    "number_of_replicas": 0,    # No replicas for dev
    "analysis": {
        "analyzer": {
            "english": {
                "type": "english",
            }
        }
    },
}
```

**Production Recommendations:**
- Increase `number_of_replicas` to 1-2 for availability
- Increase `number_of_shards` for datasets > 100k documents
- Add custom analyzers for specific languages
- Enable index refresh interval optimization

### Query Optimization

1. **Use keyword fields for exact matches**
   ```python
   .filter("term", location_country__keyword="Kenya")  # Fast
   # vs
   .filter("match", location_country="Kenya")  # Slower
   ```

2. **Limit result size**
   ```python
   search[0:20]  # Limit to 20 results
   ```

3. **Select only needed fields**
   ```python
   search.source(["post_number", "post_name", "organization"])
   ```

4. **Use filters instead of queries when possible**
   - Filters are cached and faster
   - Use for exact matches, ranges, exists checks

5. **Pagination with search_after**
   For deep pagination, use `search_after` instead of `from/size`

## Troubleshooting

### Connection Errors

**Issue**: Cannot connect to Elasticsearch

```python
elasticsearch.exceptions.ConnectionError
```

**Solution**:
1. Check Elasticsearch is running: `docker ps`
2. Verify port is accessible: `curl http://localhost:9200`
3. Check `ELASTICSEARCH_DSL_HOSTS` in settings

### Index Not Found

**Issue**: `index_not_found_exception`

**Solution**:
```bash
python manage.py search_index --create
python manage.py rebuild_index
```

### Documents Not Indexing

**Issue**: New JobAdvertisements not appearing in search

**Solution**:
1. Check `ELASTICSEARCH_DSL_AUTOSYNC` is `True`
2. Verify signals are registered in `core/apps.py`
3. Manually rebuild: `python manage.py rebuild_index`

### Out of Memory

**Issue**: Elasticsearch crashes or becomes slow

**Solution**:
1. Increase heap size in `docker-compose.yml`:
   ```yaml
   ES_JAVA_OPTS: "-Xms1g -Xmx1g"
   ```
2. Reduce data volume or use pagination

### Stale Data

**Issue**: Search returns outdated information

**Solution**:
1. Refresh index manually:
   ```python
   from core.documents import JobAdvertisementDocument
   JobAdvertisementDocument._index.refresh()
   ```
2. Rebuild index: `python manage.py rebuild_index --delete`

## Security Considerations

### Development

Current setup has security disabled:
```yaml
xpack.security.enabled=false
```

This is acceptable for local development.

### Production

For production deployment:

1. **Enable X-Pack Security**
   ```yaml
   xpack.security.enabled=true
   ```

2. **Set up authentication**
   ```bash
   docker exec -it unjobatlas_elasticsearch \
     bin/elasticsearch-setup-passwords auto
   ```

3. **Update Django settings**
   ```python
   ELASTICSEARCH_DSL = {
       "default": {
           "hosts": ["https://elasticsearch:9200"],
           "http_auth": ("username", "password"),
           "use_ssl": True,
           "verify_certs": True,
       }
   }
   ```

4. **Use environment variables**
   ```bash
   ELASTICSEARCH_DSL_USERNAME=elastic
   ELASTICSEARCH_DSL_PASSWORD=your-secure-password
   ```

## Future Enhancements

Potential improvements:

1. **Geolocation Search**: Add geo-point field for location-based search
2. **Relevance Tuning**: Custom scoring with function_score
3. **Synonyms**: Add synonym analyzer for better matching
4. **Highlights**: Show matched text snippets in results
5. **Faceted Search**: Pre-computed aggregations for filtering
6. **Query Suggestions**: "Did you mean?" functionality
7. **Analytics**: Track popular searches and results
8. **Multi-language**: Language-specific analyzers
9. **Saved Searches**: Allow users to save and subscribe to searches
10. **Related Jobs**: "More like this" recommendations

## References

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Django-Elasticsearch-DSL Documentation](https://django-elasticsearch-dsl.readthedocs.io/)
- [Elasticsearch DSL Python](https://elasticsearch-dsl.readthedocs.io/)
