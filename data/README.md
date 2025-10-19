# Data Directory

## Files
- `my_cv.txt` - Sample CV
- `target_job.txt` - Sample job description

## Usage
Replace sample files with your own CV and job descriptions.

Supported formats: `.txt`, `.pdf`, `.docx`

## Testing
```bash
python3 -c "
from src.python_advanced_job_engine import AdvancedJobEngine
engine = AdvancedJobEngine()
print('CV:', len(engine.read_document('data/my_cv.txt').split()), 'words')
print('Job:', len(engine.read_document('data/target_job.txt').split()), 'words')
"
```
