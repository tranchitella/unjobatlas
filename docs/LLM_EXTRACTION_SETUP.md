# LLM-Based Job Data Extraction Setup

## Overview

This document describes the implementation of an LLM-based extraction pipeline for processing job advertisement data. The system uses OpenAI's GPT-4 to extract structured information from job postings and automatically create `JobAdvertisement` records.

## Architecture

The processing pipeline consists of two main stages:

### Stage 1: Content Download (Existing, Modified)
- **Trigger**: When a `RawJobData` record is created with status `PENDING`
- **Task**: `process_raw_job_data`
- **Process**:
  1. Updates status to `DOWNLOADING`
  2. Downloads job posting content using Playwright
  3. Converts HTML to Markdown
  4. Updates status to `DOWNLOADED`
  5. Saves extracted content to `RawJobData` record

### Stage 2: LLM Extraction (New)
- **Trigger**: When a `RawJobData` record status changes to `DOWNLOADED`
- **Task**: `extract_job_data`
- **Process**:
  1. Updates status to `PROCESSING`
  2. Sends job content to OpenAI API
  3. Parses structured JSON response
  4. Creates `Organization` (if needed)
  5. Creates `JobAdvertisement` record
  6. Creates `LanguageRequirement` records
  7. Updates status to `PROCESSED`
  8. Links `JobAdvertisement` to `RawJobData`

## Status Flow

```
PENDING → DOWNLOADING → DOWNLOADED → PROCESSING → PROCESSED
                                                 ↘ FAILED
```

## New Status Values

Added to `RawJobData.Statuses`:
- `DOWNLOADING = "Downloading Content"` - Content download in progress
- `DOWNLOADED = "Content Downloaded"` - Content ready for LLM extraction

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Settings

Added to `config/settings.py`:

```python
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
```

### Dependencies

Added to `requirements.txt`:

```
openai>=2.8.1
```

Install with:

```bash
pip install -r requirements.txt
```

## LLM Prompt Design

The extraction uses a carefully designed prompt with the following features:

### Few-Shot Learning
- Provides a complete example of the expected JSON output
- Shows the correct format for all fields including nested structures
- Demonstrates how to handle null values

### Anti-Hallucination Measures
1. **Explicit Instructions**: "ONLY extract information that is explicitly stated"
2. **Null Handling**: "If a field's information is not found, use null"
3. **Format Constraints**: Uses OpenAI's `response_format={"type": "json_object"}` parameter
4. **Low Temperature**: Set to 0.1 for more deterministic output
5. **Structured Schema**: Provides exact field names and allowed values

### Extracted Fields

The LLM extracts the following information:

**Basic Information**:
- organization_name
- post_number
- date_posted (YYYY-MM-DD)
- application_deadline (YYYY-MM-DD)
- post_name (job title)

**Contract Details**:
- contract_type (consultant, temporary, fixed_term, internship, volunteering, other)
- contract_duration
- renewable (boolean)

**Location**:
- location_region
- location_country
- location_city
- work_arrangement (on-site, remote, hybrid)

**Position Details**:
- thematic_area
- position_level (P-3, NO-2, G-5, etc.)
- brief_description (2-3 sentence summary)

**Requirements**:
- main_skills_competencies
- technical_skills
- minimum_academic_qualifications
- minimum_experience
- language_requirements (array of objects)

**Metadata**:
- tags (array of relevant keywords)

## Signal Configuration

Two signals handle the processing pipeline:

### 1. `trigger_job_processing` (existing, unchanged)
```python
@receiver(post_save, sender=RawJobData)
def trigger_job_processing(sender, instance, created, **kwargs):
    if created and instance.status == RawJobData.Statuses.PENDING:
        process_raw_job_data.delay(instance.id)
```

### 2. `trigger_job_extraction` (new)
```python
@receiver(post_save, sender=RawJobData)
def trigger_job_extraction(sender, instance, created, update_fields, **kwargs):
    if not created and instance.status == RawJobData.Statuses.DOWNLOADED:
        extract_job_data.delay(instance.id)
```

## Error Handling

Both tasks include robust error handling:

### Retry Logic
- **Download Task**: Max 5 retries with 60s base countdown, exponential backoff
- **Extraction Task**: Max 3 retries with 120s base countdown, exponential backoff

### Error States
- Errors are logged to `processing_error` field
- Status updates to `FAILED` on final retry exhaustion
- Detailed logging for debugging

### Fallback Values
- If `date_posted` is missing, uses `crawled_at` date
- If `application_deadline` is missing, uses current date + 30 days
- If organization name is missing, uses "Unknown Organization"

## Database Migration

A migration has been created to add the new status choices:

```bash
python manage.py migrate core
```

Migration file: `core/migrations/0003_add_downloading_downloaded_status.py`

## Usage

### Manual Testing

To test the extraction on existing records:

```python
from core.models import RawJobData
from core.tasks import extract_job_data

# Get a downloaded record
raw_job = RawJobData.objects.filter(status='Content Downloaded').first()

# Trigger extraction
extract_job_data.delay(raw_job.id)
```

### Monitoring

Monitor the processing pipeline:

```python
from core.models import RawJobData

# Check status distribution
RawJobData.objects.values('status').annotate(count=Count('id'))

# Find failed records
RawJobData.objects.filter(status='Processing Failed')

# Check processing errors
failed = RawJobData.objects.filter(status='Processing Failed')
for job in failed:
    print(f"{job.post_number}: {job.processing_error}")
```

## Cost Considerations

### OpenAI API Usage

- **Model**: GPT-4 (gpt-4o)
- **Estimated tokens per job**: ~2,000-4,000 tokens (input) + 500-1,000 tokens (output)
- **Cost per job**: ~$0.01-0.03 USD (varies by content length)

### Optimization Tips

1. **Content Truncation**: Job content is limited to 8,000 characters in the prompt
2. **Batch Processing**: Celery allows parallel processing with rate limiting
3. **Caching**: Failed extractions can be retried without re-downloading content

## Future Enhancements

Potential improvements:

1. **Model Selection**: Add configuration to switch between GPT-4, GPT-3.5, or other models
2. **Validation Layer**: Add post-extraction validation to catch malformed data
3. **Human Review**: Flag uncertain extractions for manual review
4. **Fine-tuning**: Fine-tune a model on validated job postings for better accuracy
5. **Structured Outputs**: Use OpenAI's structured outputs feature when available
6. **Incremental Updates**: Support updating existing JobAdvertisement records

## Troubleshooting

### Common Issues

**Issue**: OpenAI API rate limit errors
- **Solution**: Reduce Celery worker concurrency or add rate limiting

**Issue**: Invalid JSON response from LLM
- **Solution**: Check the `processing_error` field for details, may need prompt adjustment

**Issue**: Missing field data in extracted JSON
- **Solution**: Verify the job posting contains the information; LLM correctly returns null for missing data

**Issue**: Extraction task not triggered
- **Solution**: Ensure the signal is registered in `core/apps.py` and status changes to `DOWNLOADED`

## Security Considerations

1. **API Key Protection**: Never commit `.env` file with real API key
2. **Content Sanitization**: Job content is not sanitized before sending to OpenAI
3. **PII Handling**: Job postings may contain personal information in examples
4. **Rate Limiting**: Implement rate limiting to prevent abuse

## References

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Celery Best Practices](https://docs.celeryq.dev/en/stable/userguide/tasks.html)
- [Django Signals](https://docs.djangoproject.com/en/stable/topics/signals/)
