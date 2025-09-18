# ChromeDriver Troubleshooting & Reverse Image Search Reliability

The genuine reverse image search pipeline relies on Selenium + Chrome. Recent failures were caused by a version mismatch:

```
This version of ChromeDriver only supports Chrome version 138
Current browser version is 140.x.x
```

## Fast Fix (Recommended)
The code now attempts an automatic fallback using Selenium Manager when a mismatch is detected. Steps:
1. Re-run your pipeline normally. If a mismatch is logged, the engine will try to rename a stale Homebrew driver at `/opt/homebrew/bin/chromedriver` (adding `.disabled`).
2. Selenium will then download a matching driver automatically.

If the fallback succeeds you should see:
```
⚠️ Detected Chrome/ChromeDriver mismatch. Attempting fallback cleanup and retry via Selenium Manager.
Renamed stale chromedriver ...
✅ Browser setup complete for genuine OSINT
```

## Manual Recovery (If Automatic Fallback Fails)
1. Remove or rename the existing driver:
   ```bash
   mv /opt/homebrew/bin/chromedriver /opt/homebrew/bin/chromedriver.manual_backup
   ```
2. Clear any cached Selenium drivers (optional):
   ```bash
   rm -rf ~/Library/Caches/selenium
   ```
3. Re-run the pipeline. Selenium Manager should provision the correct binary.

## Force Visible Browser (Debug Mode)
Set an environment variable to watch interactions live:
```bash
export OSINT_VISIBLE_BROWSER=1
python run_pipeline_baseline_and_enhanced.py --images 4d_models --outdir exports
```
Unset or set to 0 to return to headless mode.

## Common Issues
| Symptom | Cause | Resolution |
|---------|-------|------------|
| `session not created` | Version mismatch | Let fallback rename driver or remove manually |
| Hangs on Google/Yandex page load | Network / geolocation block | Increase implicit wait, test network separately |
| 0 URLs consistently | Selectors changed | Update CSS selectors in `_search_*` methods |
| Many inaccessible URLs | Sites blocking HEAD | The engine falls back to GET automatically |

## Verifying Driver Version
Run:
```bash
chromedriver --version || echo 'No chromedriver on PATH'
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```
Versions should share the same major number (e.g. both 140).

## If You Need a Pinned Driver
You can still install a specific version:
```bash
brew remove --force chromedriver
brew install --cask chromedriver@140  # example if available
```
(Then ensure your Chrome major version matches.)

## Disabling Reverse Image Search (Faster Runs)
Use the baseline flags already present:
```bash
python run_pipeline_baseline_and_enhanced.py --images 4d_models --outdir exports --osint-only
```
This skips 3D/4D generation AND still performs reverse searches (unless baseline mode disables them). To fully disable reverse search in custom code, pass `disable_reverse_search=True` to `Complete4DOSINTPipeline`.

## Notes on Reliability
- Selenium Manager (bundled with Selenium 4.10+) eliminates most manual driver management.
- Headless Chrome recently changed flags (`--headless=new` now preferred). The engine uses this for stability.
- A visible session (`OSINT_VISIBLE_BROWSER=1`) is invaluable while adjusting selectors.

## Next Improvements (Future)
- Add per-engine timeout tuning
- Structured retry with exponential backoff
- Optional proxy / rotating user-agents

If issues persist, capture the first 50 lines of the log and search for `ChromeDriver` or `session not created` to confirm mismatch handling executed.
