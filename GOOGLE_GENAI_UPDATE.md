# Package Update: google-generativeai → google-genai

## What Changed

Google has deprecated the `google-generativeai` package in favor of the new `google-genai` package.

## Files Updated

1. **requirements.txt** - Changed dependency from `google-generativeai` to `google-genai`
2. **tradingagents/agents/utils/memory.py** - Updated import and API usage
3. **tests/test_setup.py** - Updated import check
4. **Documentation files** - Updated references

## API Changes

### Old (Deprecated)
```python
import google.generativeai as genai

genai.configure(api_key=api_key)
result = genai.embed_content(
    model="models/text-embedding-004",
    content=text,
    task_type="retrieval_document"
)
embedding = result['embedding']
```

### New (Current)
```python
from google import genai

client = genai.Client(api_key=api_key)
result = client.models.embed_content(
    model="text-embedding-004",
    content=text
)
embedding = result.embeddings[0].values
```

## Action Required

```bash
# Update dependencies
pip install -r requirements.txt

# Test the update
python tests/test_setup.py
```

That's it! The code has been updated and should work seamlessly with the new package.

