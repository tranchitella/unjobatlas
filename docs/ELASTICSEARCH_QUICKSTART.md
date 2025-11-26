# Elasticsearch Quick Start

## Start Services

```bash
# Start all services (PostgreSQL, Redis, Elasticsearch)
docker-compose up -d

# Check all services are healthy
docker-compose ps
```

## Setup Elasticsearch Index

```bash
# Install Python dependencies (if not already installed)
pip install -r requirements.txt

# Create the Elasticsearch index
python manage.py search_index --create

# Index all existing JobAdvertisement records
python manage.py rebuild_index
```

## Verify Setup

```bash
# Check Elasticsearch is running
curl http://localhost:9200

# Check cluster health
curl http://localhost:9200/_cluster/health?pretty

# Check index exists
curl http://localhost:9200/_cat/indices?v

# Count indexed documents
curl http://localhost:9200/job_advertisements/_count?pretty
```

## Basic Search Examples

### Python/Django

```python
from core.documents import JobAdvertisementDocument

# Search all jobs
search = JobAdvertisementDocument.search()
results = search.execute()

# Search by job title
search = JobAdvertisementDocument.search()
results = search.query("match", post_name="Programme Officer")

# Filter by country
search = JobAdvertisementDocument.search()
results = search.filter("term", location_country__keyword="Kenya")

# Active jobs only
from datetime import date
search = JobAdvertisementDocument.search()
results = search.filter("range", application_deadline={"gte": date.today()})

# Execute and iterate
for hit in results:
    print(f"{hit.post_number}: {hit.post_name}")
```

### REST API

```bash
# Search by job title
curl -X GET "http://localhost:9200/job_advertisements/_search?pretty" \
  -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "post_name": "Programme Officer"
    }
  }
}
'

# Filter by country
curl -X GET "http://localhost:9200/job_advertisements/_search?pretty" \
  -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "location_country.keyword": "Kenya"
    }
  }
}
'

# Get active jobs
curl -X GET "http://localhost:9200/job_advertisements/_search?pretty" \
  -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "application_deadline": {
              "gte": "now"
            }
          }
        }
      ]
    }
  }
}
'
```

## Rebuild Index

If data gets out of sync:

```bash
# Delete and rebuild index
python manage.py rebuild_index --delete

# Or use Django-Elasticsearch-DSL command
python manage.py search_index --rebuild
```

## Troubleshooting

### Elasticsearch not starting

```bash
# Check logs
docker logs unjobatlas_elasticsearch

# Ensure enough memory
# Edit docker-compose.yml if needed:
# ES_JAVA_OPTS: "-Xms1g -Xmx1g"
```

### Index not found

```bash
# Create the index
python manage.py search_index --create
python manage.py rebuild_index
```

### Data not appearing in search

```bash
# Refresh the index
curl -X POST "http://localhost:9200/job_advertisements/_refresh"

# Or rebuild completely
python manage.py rebuild_index --delete
```

## Next Steps

- See [ELASTICSEARCH_SETUP.md](./ELASTICSEARCH_SETUP.md) for detailed documentation
- Implement search API endpoints for your frontend
- Add faceted search and filters
- Implement autocomplete functionality

## Common Queries

### Search across multiple fields

```python
from elasticsearch_dsl import Q

search = JobAdvertisementDocument.search()
query = Q("multi_match", 
    query="child protection emergency",
    fields=["post_name", "brief_description", "main_skills_competencies"]
)
results = search.query(query)
```

### Aggregations (facets)

```python
search = JobAdvertisementDocument.search()
search.aggs.bucket("by_country", "terms", field="location_country.keyword", size=20)
search.aggs.bucket("by_organization", "terms", field="organization.name.keyword")
search.aggs.bucket("by_position_level", "terms", field="position_level")

results = search.execute()

# Access aggregations
for bucket in results.aggregations.by_country.buckets:
    print(f"{bucket.key}: {bucket.doc_count} jobs")
```

### Complex filters

```python
from datetime import date
from elasticsearch_dsl import Q

search = JobAdvertisementDocument.search()

# Organization: UNICEF or WFP
# Country: Kenya or Uganda
# Active jobs only
# Contract: Fixed-term

search = search.filter("terms", organization__name__keyword=["UNICEF", "WFP"])
search = search.filter("terms", location_country__keyword=["Kenya", "Uganda"])
search = search.filter("range", application_deadline={"gte": date.today()})
search = search.filter("term", contract_type="fixed_term")

results = search.execute()
```
