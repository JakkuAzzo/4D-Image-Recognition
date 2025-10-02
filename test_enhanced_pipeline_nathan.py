import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("APP_BASE_URL", "https://localhost:8000")
TARGET_URL = f"{BASE_URL}/static/enhanced-pipeline.html"
NATHAN_DIR = Path(__file__).parent / "tests" / "test_images" / "nathan"
ARTIFACTS_DIR = Path(__file__).parent / "ENHANCED_PIPELINE_ARTIFACTS"


def wait_for_status(page, step: int, timeout_ms: int = 300_000):
    selector = f"#step{step}-status.status-completed"
    page.wait_for_selector(selector, state="visible", timeout=timeout_ms)


def collect_similarity_cells(page):
    try:
        cells = page.query_selector_all("#similarity-matrix .similarity-cell")
        return [c.inner_text().strip() for c in cells][:200]  # cap to avoid huge logs
    except Exception:
        return []


def main(headless: bool = True):
    assert NATHAN_DIR.exists(), f"Nathan images folder not found: {NATHAN_DIR}"
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--ignore-certificate-errors"])
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        page.goto(TARGET_URL, wait_until="domcontentloaded")
        # The file input is hidden; only wait for it to be attached, not visible
        page.wait_for_selector("#file-input", state="attached", timeout=30000)

        # Defensive init: the script binds DOMContentLoaded inside itself, but since it's loaded at the end of body,
        # that event may have already fired. Proactively initialize upload area and ThreeJS.
        page.evaluate(
            "() => { try { if (typeof initializeUploadArea==='function') initializeUploadArea(); if (typeof initializeThreeJS==='function') initializeThreeJS(); } catch(e) { console.error('init error', e); } }"
        )

        # Pick a subset of Nathan images (prefer JPG/JPEG first to avoid large PNG screenshots)
        image_paths = []
        for ext in ("*.jpg", "*.jpeg"):
            image_paths += list(NATHAN_DIR.glob(ext))
        # If not enough, then include PNG screenshots last
        if len(image_paths) < 4:
            image_paths += list(NATHAN_DIR.glob("*.png"))
        # Include ID card too if present
        id_card = NATHAN_DIR / "id card" / "nathanIDcard.png"
        if id_card.exists():
            image_paths.append(id_card)

        # Limit to first 8 to keep pipeline responsive
        image_paths = image_paths[:8]
        assert image_paths, "No images found to upload."

        # Upload via hidden input; then invoke the page's own handler to populate selectedFiles
        file_input = page.locator("#file-input")
        file_input.set_input_files([str(p) for p in image_paths])
        page.evaluate(
            "() => { try { const fi = document.getElementById('file-input'); if (fi && fi.files && fi.files.length) { if (typeof handleFileSelection==='function') { handleFileSelection(Array.from(fi.files)); } else if (typeof executeStep1==='function') { executeStep1(); } } } catch(e) { console.error('file select error', e); } }"
        )

        # Do NOT click the Start Complete Pipeline button; drive steps explicitly

        # The page auto-starts Step 1 on file selection
        report = {
            "url": TARGET_URL,
            "images": [p.name for p in image_paths],
            "timestamps": {},
            "steps": {},
        }

        # Capture browser console logs and API responses for diagnostics
        console_logs = []
        page.on("console", lambda msg: console_logs.append({"type": msg.type, "text": msg.text}))
        responses = []
        def _resp(r):
            url = r.url
            if "/api/pipeline/" in url:
                try:
                    responses.append({"url": url, "status": r.status, "ok": r.ok})
                except Exception:
                    responses.append({"url": url, "status": r.status})
        context.on("response", _resp)

        # Quick debug snapshot of page state
        try:
            report["debug"] = {
                "has_handleFileSelection": page.evaluate("() => typeof handleFileSelection === 'function'"),
                "has_executeStep1": page.evaluate("() => typeof executeStep1 === 'function'"),
                "selectedFiles_len": page.evaluate("() => (window.selectedFiles && window.selectedFiles.length) || 0"),
                "file_input_count": page.evaluate("() => { const fi = document.getElementById('file-input'); return (fi && fi.files) ? fi.files.length : 0 }"),
            }
        except Exception:
            pass

        # Kick off step 1 explicitly and ensure it begins (processing/completed) before full wait loop
        try:
            page.evaluate("() => { if (typeof executeStep1==='function') executeStep1(); }")
            page.wait_for_function(
                "() => { const el = document.getElementById('step1-status'); if(!el) return false; const c = el.className || ''; return c.includes('status-processing') || c.includes('status-completed'); }",
                timeout=90_000,
            )
        except Exception:
            # capture error state
            try:
                err_txt = page.inner_text('#error-message') if page.is_visible('#error-message') else ''
            except Exception:
                err_txt = ''
            report["pre_step1_error"] = err_txt

        # Wait for each step to complete (sequentially trigger if needed)
        step_status_snapshot = {}
        try:
            for step in range(1, 8):
                t0 = time.time()
                # If step not yet started and an explicit executor exists, call it
                try:
                    started = page.evaluate(f"() => {{ const el = document.getElementById('step{step}-status'); if(!el) return false; const c = el.className || ''; return c.includes('status-processing') || c.includes('status-completed'); }}")
                except Exception:
                    started = False
                if not started:
                    try:
                        page.evaluate(f"(s) => {{ const fn = window['executeStep'+s]; if (typeof fn==='function') fn(); }}", step)
                    except Exception:
                        pass

                wait_for_status(page, step)
                dt = time.time() - t0
                report["timestamps"][f"step{step}_seconds"] = round(dt, 2)
                report["steps"][f"step{step}"] = "completed"
                # snapshot classes
                cls = page.get_attribute(f"#step{step}-status", "class") or ""
                step_status_snapshot[f"step{step}"] = cls
        except Exception as e:
            report["wait_error"] = str(e)
        finally:
            report["console_logs"] = console_logs[-200:]
            report["api_responses"] = responses[-50:]
            report["step_status_snapshot"] = step_status_snapshot

        # Evidence collection
        osint = {
            "similarity_matrix_present": page.is_visible("#similarity-matrix"),
            "similarity_cells_sample": collect_similarity_cells(page),
            "filtering_results_present": page.is_visible("#filtering-results"),
            "final_model_info_present": page.is_visible("#final-model-info"),
            "threejs_container_present": page.is_visible("#threejs-container"),
        }

        # Look for plausible OSINT features text in final model info
        try:
            final_text = page.inner_text("#final-model-info")
        except Exception:
            final_text = ""
        osint["final_model_info_text"] = final_text[:2000]
        osint["geometry_hash_detected"] = ("Geometry Hash" in final_text) or ("facial_geometry_hash" in final_text)
        osint["biometric_template_mentioned"] = ("Biometric Template" in final_text) or ("biometric" in final_text.lower())

        report["osint"] = osint

        # Save artifacts regardless of success
        try:
            screenshot_path = ARTIFACTS_DIR / "enhanced_pipeline_final.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            report["screenshot"] = str(screenshot_path)
        except Exception:
            pass

        report_path = ARTIFACTS_DIR / "ENHANCED_PIPELINE_NATHAN_REPORT.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(json.dumps(report, indent=2))

        context.close()
        browser.close()


if __name__ == "__main__":
    headless_flag = True
    if len(sys.argv) > 1 and sys.argv[1] == "--headed":
        headless_flag = False
    main(headless=headless_flag)
