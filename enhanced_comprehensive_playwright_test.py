#!/usr/bin/env python3
"""
Enhanced Comprehensive 4D Pipeline Playwright Test - HTTPS Version
==================================================================
Automates the end-to-end validation of the enhanced 4D OSINT pipeline.

Key checkpoints:
- HTTPS server availability and certificate handling
- Image ingestion, metadata, and compliance summaries
- Seven-step pipeline completion with per-step screenshots
- Real-data provenance via exported JSON metrics within the DOM
- 3D model viewer readiness and essential UI affordances
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Page, async_playwright


class Enhanced4DPipelinePlaywrightTest:
	"""Encapsulates the enhanced Playwright workflow for the 4D pipeline."""

	def __init__(self) -> None:
		self.base_url = "https://localhost:8000"
		self.pipeline_url = f"{self.base_url}/static/enhanced-pipeline.html"
		self.project_root = Path(
			"/Users/nathanbrown-bennett/4D-Image-Recognition/4D-Image-Recognition"
		)
		self.test_images_dir = (
			self.project_root / "tests" / "test_images" / "nathan"
		)
		self.screenshot_dir = (
			self.project_root
			/ "ENHANCED_PIPELINE_ARTIFACTS"
			/ "playwright_screenshots"
		)
		self.screenshot_dir.mkdir(parents=True, exist_ok=True)

		self.server_process: Optional[subprocess.Popen[str]] = None
		self.test_results: Dict[str, Any] = {}

	# ------------------------------------------------------------------
	# Server lifecycle helpers
	# ------------------------------------------------------------------
	async def start_https_server(self) -> bool:
		"""Start the HTTPS development server via the provided shell script."""

		if self.server_process and self.server_process.poll() is None:
			# Already running
			return True

		print("🚀 Starting HTTPS development server...")
		try:
			self.server_process = subprocess.Popen(
				["sh", "run_https_dev.sh"],
				cwd=self.project_root,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				text=True,
				preexec_fn=os.setsid,
			)

			# Allow the server a moment to bind to the port
			await asyncio.sleep(10)

			try:
				import requests
				import urllib3

				urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
				response = requests.get(self.base_url, verify=False, timeout=5)
				if response.status_code == 200:
					print("✅ HTTPS server responded successfully")
					return True
			except Exception:
				# Even if the probe fails we optimistically continue; Playwright will retry.
				print("⏳ HTTPS server probe failed, continuing optimistically")
				return True

		except Exception as exc:  # pragma: no cover - defensive logging
			print(f"❌ Failed to start HTTPS server: {exc}")
			return False

		return True

	async def stop_server(self) -> None:
		"""Terminate the HTTPS development server if it was started."""

		if not self.server_process:
			return

		print("🛑 Stopping HTTPS development server...")
		try:
			os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
			await asyncio.sleep(2)
			if self.server_process.poll() is None:
				os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
		except Exception as exc:  # pragma: no cover - defensive logging
			print(f"⚠️  Error while stopping server: {exc}")
		finally:
			self.server_process = None
			print("✅ HTTPS server stopped")

	async def _ensure_https_backend(self) -> bool:
		"""Ensure the HTTPS backend is reachable, starting it when necessary."""

		try:
			import requests
			import urllib3

			urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
			response = requests.get(self.base_url, verify=False, timeout=5)
			if response.status_code == 200:
				print("✅ HTTPS backend already online")
				return True
		except Exception:
			pass

		print("🔁 HTTPS backend unavailable; attempting to launch it")
		return await self.start_https_server()

	# ------------------------------------------------------------------
	# Browser utilities
	# ------------------------------------------------------------------
	async def ensure_pipeline_page(self, page: Page) -> None:
		"""Navigate to the enhanced pipeline page and wait for the upload UI."""

		if "enhanced-pipeline" not in page.url:
			await page.goto(self.pipeline_url, wait_until="domcontentloaded", timeout=20000)

		await page.wait_for_selector("#file-input", state="attached", timeout=20000)

	async def capture_step_screenshot(self, page: Page, step_num: int, *, suffix: str = "completed") -> Dict[str, Any]:
		"""Capture and validate a screenshot for a given pipeline step container."""

		selector = f"#step{step_num}-container"
		file_path = self.screenshot_dir / f"step{step_num:02d}_{suffix}.png"
		capture: Dict[str, Any] = {"path": str(file_path), "valid": False}

		try:
			await page.wait_for_selector(selector, state="visible", timeout=30000)
			await page.locator(selector).scroll_into_view_if_needed()
			await page.wait_for_timeout(250)
			await page.locator(selector).screenshot(path=str(file_path))
			size = file_path.stat().st_size if file_path.exists() else 0
			capture.update({"size_bytes": size, "valid": size > 1024})
			note = "valid" if capture["valid"] else "too small"
			print(f"   📸 Step {step_num} screenshot captured ({size} bytes, {note})")
		except Exception as exc:
			capture["error"] = str(exc)
			print(f"   ❌ Screenshot capture failed for step {step_num}: {exc}")

		self.test_results.setdefault("step_screenshots", {})[f"step{step_num}"] = capture
		return capture

	async def _evaluate_loader_snapshot(self, page: Page) -> Dict[str, Any]:
		"""Inspect overlay/skeleton state and pipeline data presence."""

		try:
			snapshot = await page.evaluate(
				"""
				() => {
					const overlayEl = document.getElementById('loading-overlay');
					let overlayVisible = false;
					if (overlayEl) {
						const style = window.getComputedStyle(overlayEl);
						overlayVisible = style ? style.display !== 'none' : false;
					}

					const skeletonNodes = Array.from(document.querySelectorAll('[class*="skeleton"]'));
					const pipelineData = window.pipelineData || {};
					const result = {
						overlay_visible: overlayVisible,
						skeleton_count: skeletonNodes.length,
						skeleton_samples: skeletonNodes.slice(0, 3).map((node) => node.id || node.className || node.tagName),
						pipeline_keys: Object.keys(pipelineData),
						step_data_presence: {},
						step_status_text: {},
						progress_text: (document.getElementById('progress-text')?.textContent || '').trim() || null,
					};

					for (let step = 1; step <= 7; step += 1) {
						const key = `step${step}`;
						const stepData = pipelineData[key];
						const statusEl = document.getElementById(`${key}-status`);
						result.step_data_presence[key] = {
							has_data: !!stepData,
							keys: stepData && typeof stepData === 'object' ? Object.keys(stepData) : [],
							image_count: stepData && Array.isArray(stepData.images) ? stepData.images.length : null,
						};
						result.step_status_text[key] = statusEl ? (statusEl.textContent || '').trim() : null;
					}

					return result;
				}
				"""
			)
			snapshot["timestamp"] = time.strftime("%H:%M:%S")
			return snapshot
		except Exception as exc:  # pragma: no cover - defensive logging
			print(f"   ⚠️ Loader snapshot capture failed: {exc}")
			return {"error": str(exc)}

	async def _wait_for_step_completion(self, page: Page, step_num: int) -> bool:
		"""Wait until a pipeline step badge reports completion."""

		badge_selector = f"#step{step_num}-status"
		try:
			await page.wait_for_selector(badge_selector, timeout=45000)
			await page.wait_for_function(
				"selector => {\n                    const el = document.querySelector(selector);\n                    if (!el) return false;\n                    const text = (el.textContent || '').toLowerCase();\n                    return text.includes('completed');\n                }",
				arg=badge_selector,
				timeout=120000,
			)
			return True
		except Exception as exc:
			print(f"   ❌ Step {step_num} did not reach completed state: {exc}")
			return False

	# ------------------------------------------------------------------
	# Individual test components
	# ------------------------------------------------------------------
	async def get_test_images(self) -> List[Path]:
		"""Locate Nathan's curated test images."""

		if not self.test_images_dir.exists():
			print(f"❌ Test images directory missing: {self.test_images_dir}")
			return []

		image_files: List[Path] = []
		for glob in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
			image_files.extend(self.test_images_dir.glob(glob))

		image_files.sort()
		print(f"📁 Found {len(image_files)} candidate images for upload")
		for preview in image_files[:5]:
			print(f"   • {preview.name}")
		if len(image_files) > 5:
			print(f"   • …and {len(image_files) - 5} more")

		return image_files

	async def test_https_accessibility(self, page: Page) -> bool:
		print("\n🔒 Verifying HTTPS server accessibility")
		try:
			response = await page.goto(self.base_url, wait_until="networkidle", timeout=20000)
			ok = response is not None and response.status == 200
			self.test_results["https_accessible"] = ok
			print("✅ HTTPS endpoint reachable" if ok else "❌ HTTPS endpoint unreachable")
			return ok
		except Exception as exc:
			self.test_results["https_accessible"] = False
			print(f"❌ HTTPS accessibility check failed: {exc}")
			return False

	async def test_unified_pipeline_loading(self, page: Page) -> bool:
		print("\n🌐 Checking enhanced pipeline shell loads correctly")
		try:
			await self.ensure_pipeline_page(page)
			await page.wait_for_timeout(1000)

			checks = {
				"upload_section": await page.is_visible("#upload-area"),
				"step_containers": (await page.locator(".pipeline-container").count()) >= 7,
				"start_button": (await page.locator("#start-pipeline").count()) > 0,
				"progress_text": (await page.locator("#progress-text").count()) == 1,
				"summary_panel": (await page.locator("#step1-summary").count()) == 1,
				"threejs_container": (await page.locator("#threejs-container").count()) == 1,
			}

			print("Enhanced shell component checks:")
			for key, value in checks.items():
				print(f"   • {key.replace('_', ' ').title()}: {'✅' if value else '❌'}")

			success = all(checks.values())
			self.test_results["unified_pipeline_loading"] = {"checks": checks, "success": success}
			return success
		except Exception as exc:
			print(f"❌ Pipeline shell failed to load: {exc}")
			self.test_results["unified_pipeline_loading"] = {"success": False, "error": str(exc)}
			return False

	async def test_enhanced_file_upload(self, page: Page, image_files: List[Path]) -> bool:
		print(f"\n📤 Uploading images ({len(image_files)} found)")
		try:
			await self.ensure_pipeline_page(page)

			file_input = page.locator("#file-input")
			await file_input.set_input_files([str(p) for p in image_files[:6]])
			pre_summary_snapshot = await self._evaluate_loader_snapshot(page)
			await page.wait_for_selector("#step1-summary", timeout=35000)
			post_summary_snapshot = await self._evaluate_loader_snapshot(page)

			checks = {
				"ingested_cards": (await page.locator("#ingested-images .image-card").count()) > 0,
				"progress_text": "Uploaded" in (await page.locator("#progress-text").text_content() or ""),
			}

			print("Upload phase loader snapshots:")
			for label, snap in (("pre-summary", pre_summary_snapshot), ("post-summary", post_summary_snapshot)):
				if "error" in snap:
					print(f"   • {label}: ❌ snapshot error -> {snap['error']}")
					continue
				print(
					f"   • {label}: overlay={'ON' if snap['overlay_visible'] else 'off'}, "
					f"skeletons={snap['skeleton_count']}, pipeline_keys={len(snap['pipeline_keys'])}, "
					f"step1_has_data={snap['step_data_presence'].get('step1', {}).get('has_data')}"
				)

			for key, value in checks.items():
				print(f"   • {key.replace('_', ' ').title()}: {'✅' if value else '❌'}")

			success = all(checks.values())
			self.test_results["upload_phase_state"] = {
				"pre_summary": pre_summary_snapshot,
				"post_summary": post_summary_snapshot,
			}
			self.test_results["enhanced_file_upload"] = {"checks": checks, "success": success}
			return success
		except Exception as exc:
			print(f"❌ Enhanced upload failed: {exc}")
			self.test_results["enhanced_file_upload"] = {"success": False, "error": str(exc)}
			return False

	async def test_complete_pipeline_execution(self, page: Page) -> bool:
		print("\n🚀 Verifying seven-step pipeline execution")

		pipeline_ok = True
		step_results: Dict[str, Any] = {}

		# Trigger the automated workflow if the start button is available
		start_button = page.locator("#start-pipeline")
		if await start_button.count():
			try:
				if await start_button.is_enabled():
					await start_button.click()
					print("   ▶️ Start button clicked")
			except Exception as exc:
				print(f"   ⚠️ Start button interaction failed: {exc}")

		for step_num in range(1, 8):
			completed = await self._wait_for_step_completion(page, step_num)
			capture = await self.capture_step_screenshot(page, step_num, suffix="completed" if completed else "error")
			loader_snapshot = await self._evaluate_loader_snapshot(page)
			badge_text = await page.locator(f"#step{step_num}-status").inner_text()
			step_results[f"step{step_num}"] = {
				"completed": completed,
				"status_text": badge_text,
				"screenshot": capture,
				"loader_snapshot": loader_snapshot,
			}
			pipeline_ok &= completed and capture.get("valid", False)

		# Verify success indicator and 3D canvas readiness
		success_banner = await page.locator("#success-message").is_visible()
		canvas_ready = (await page.locator("#threejs-container canvas").count()) > 0
		progress_text = await page.locator("#progress-text").text_content()

		pipeline_ok = pipeline_ok and success_banner and canvas_ready

		self.test_results["complete_pipeline_execution"] = {
			"steps": step_results,
			"success_banner": success_banner,
			"canvas_ready": canvas_ready,
			"progress_text": progress_text,
			"overall_success": pipeline_ok,
		}

		skeleton_detected = any(
			(step_info.get("loader_snapshot") or {}).get("skeleton_count", 0) > 0
			for step_info in step_results.values()
		)
		overlay_seen = any((step_info.get("loader_snapshot") or {}).get("overlay_visible", False) for step_info in step_results.values())
		overlay_cleared = any(
			not ((step_info.get("loader_snapshot") or {}).get("overlay_visible", False))
			for step_info in step_results.values()
		)
		self.test_results["complete_pipeline_execution"]["loader_observations"] = {
			"overlay_seen": overlay_seen,
			"overlay_cleared": overlay_cleared,
			"skeleton_detected": skeleton_detected,
		}

		print(
			"✅ All steps completed with valid screenshots"
			if pipeline_ok
			else "❌ Pipeline completion encountered issues"
		)
		return pipeline_ok

	async def test_enhanced_3d_model_viewer(self, page: Page) -> bool:
		print("\n🎭 Validating 3D model viewer state")
		try:
			await page.wait_for_selector("#step7-content", timeout=30000)
			checks = {
				"canvas_present": (await page.locator("#threejs-container canvas").count()) > 0,
				"reset_button": (await page.locator("#reset-pipeline").count()) > 0,
				"final_panel": (await page.locator("#final-model-info").count()) == 1,
			}
			canvas_dimensions = await page.evaluate(
				"() => {\n                    const canvas = document.querySelector('#threejs-container canvas');\n                    if (!canvas) return null;\n                    return { width: canvas.clientWidth, height: canvas.clientHeight };\n                }"
			)
			checks["canvas_visible"] = bool(canvas_dimensions and canvas_dimensions["width"] > 0)

			for key, value in checks.items():
				print(f"   • {key.replace('_', ' ').title()}: {'✅' if value else '❌'}")

			success = sum(checks.values()) >= len(checks) - 1 and checks["canvas_present"]
			self.test_results["enhanced_3d_model_viewer"] = {"checks": checks, "success": success}
			return success
		except Exception as exc:
			print(f"❌ 3D model viewer validation failed: {exc}")
			self.test_results["enhanced_3d_model_viewer"] = {"success": False, "error": str(exc)}
			return False

	async def test_real_data_validation(self, page: Page) -> bool:
		print("\n🔍 Inspecting DOM metrics for real-data provenance")
		try:
			snapshot: Dict[str, Any] = await page.evaluate(
				"""
				() => {
					const result = {
						hasPipelineData: typeof window.pipelineData !== 'undefined' && !!window.pipelineData,
						pipelineMetrics: null,
						scriptMetrics: {},
					};

					try {
						const data = window.pipelineData || {};
						const step1 = data.step1 || {};
						const step2 = data.step2 || {};
						const step3 = data.step3 || {};
						const step4 = data.step4 || {};
						const step5 = data.step5 || {};
						const step6 = data.step6 || {};
						const step7 = data.step7 || {};

						result.pipelineMetrics = {
							ingested_total: step1.metadata_summary && step1.metadata_summary.total_images,
							ingested_accepted: step1.compliance_summary && step1.compliance_summary.accepted,
							ingested_dropped: step1.compliance_summary && step1.compliance_summary.dropped,
							faces_detected: step2.face_detection_summary && step2.face_detection_summary.faces_detected,
							similarity_valid_faces: step3.validation_summary && step3.validation_summary.valid_faces,
							similarity_groups: Array.isArray(step3.same_person_groups) ? step3.same_person_groups.length : null,
							filtering_summary: step4.filtering_summary || null,
							isolation_count: Array.isArray(step5.isolated_faces) ? step5.isolated_faces.length : null,
							merging_summary: step6.merging_summary || null,
							refinement_summary: step7.refinement_summary || null,
							compliance_status: step7.compliance_summary && step7.compliance_summary.status,
						};
					} catch (err) {
						result.pipelineMetrics = null;
					}

					document.querySelectorAll('script[data-metrics]').forEach((node) => {
						const key = node.dataset.metrics || node.id || `metric-${Object.keys(result.scriptMetrics).length}`;
						try {
							result.scriptMetrics[key] = JSON.parse(node.textContent || 'null');
						} catch (_) {
							result.scriptMetrics[key] = null;
						}
					});

					return result;
				}
				"""
			)

			pipeline_metrics = snapshot.get("pipelineMetrics") or {}
			script_metrics = snapshot.get("scriptMetrics") or {}

			validations = {
				"pipeline_data": snapshot.get("hasPipelineData", False),
				"ingestion_totals": (pipeline_metrics.get("ingested_total") or 0) > 0,
				"compliance_counts": pipeline_metrics.get("ingested_accepted") is not None,
				"faces_detected": pipeline_metrics.get("faces_detected") is not None,
				"similarity_metrics": bool(script_metrics.get("similarity") or pipeline_metrics.get("similarity_valid_faces")),
				"orientation_metrics": bool(script_metrics.get("orientation")),
				"merging_metrics": bool(script_metrics.get("merging") or pipeline_metrics.get("merging_summary")),
				"refinement_metrics": bool(script_metrics.get("refinement") or pipeline_metrics.get("refinement_summary")),
				"compliance_script": bool(script_metrics.get("compliance")),
				"isolation_count": pipeline_metrics.get("isolation_count") is not None,
			}

			success_rate = sum(1 for value in validations.values() if value) / len(validations)

			print("Real-data metric indicators:")
			for key, value in validations.items():
				print(f"   • {key.replace('_', ' ').title()}: {'✅' if value else '❌'}")

			success = success_rate >= 0.8
			self.test_results["real_data_validation"] = {
				"validations": validations,
				"success_rate": success_rate,
				"success": success,
				"pipeline_metrics": pipeline_metrics,
				"script_metrics_keys": list(script_metrics.keys()),
			}

			print(f"📊 Real-data success rate: {success_rate:.0%}")
			return success
		except Exception as exc:
			print(f"❌ Real-data validation failed: {exc}")
			self.test_results["real_data_validation"] = {"success": False, "error": str(exc)}
			return False

	async def test_comprehensive_ui_interactions(self, page: Page) -> bool:
		print("\n🖱️ Running UI affordance smoke checks")
		try:
			checks = {
				"hover_file_input": False,
				"progress_bar": False,
				"step_headers": False,
				"reset_button": False,
			}

			file_input = page.locator("#file-input")
			try:
				await file_input.hover()
				checks["hover_file_input"] = True
			except Exception:
				pass

			try:
				checks["progress_bar"] = await page.locator("#overall-progress").is_visible()
			except Exception:
				pass

			try:
				checks["step_headers"] = (await page.locator(".step-header").count()) >= 7
			except Exception:
				pass

			try:
				checks["reset_button"] = await page.locator("#reset-pipeline").is_visible()
			except Exception:
				pass

			for key, value in checks.items():
				print(f"   • {key.replace('_', ' ').title()}: {'✅' if value else '❌'}")

			success = sum(checks.values()) >= len(checks) - 1
			self.test_results["comprehensive_ui_interactions"] = {"checks": checks, "success": success}
			return success
		except Exception as exc:
			print(f"❌ UI interaction sweep failed: {exc}")
			self.test_results["comprehensive_ui_interactions"] = {"success": False, "error": str(exc)}
			return False

	# ------------------------------------------------------------------
	# Test suite orchestration
	# ------------------------------------------------------------------
	async def run_comprehensive_test(self) -> bool:
		print("🧪 Enhanced Playwright validation starting")
		server_started_here = False

		if not await self._ensure_https_backend():
			print("❌ HTTPS backend could not be started")
			return False

		if self.server_process:
			server_started_here = True

		image_files = await self.get_test_images()
		if not image_files:
			print("❌ No input images available")
			return False

		async with async_playwright() as playwright:
			browser = await playwright.chromium.launch(
				headless=False,
				args=[
					"--ignore-certificate-errors",
					"--ignore-ssl-errors",
					"--allow-running-insecure-content",
					"--disable-web-security",
					"--disable-features=VizDisplayCompositor",
				],
				slow_mo=150,
			)

			context = await browser.new_context(
				ignore_https_errors=True,
				viewport={"width": 1920, "height": 1080},
			)
			page = await context.new_page()

			results_matrix = [
				("HTTPS accessibility", await self.test_https_accessibility(page)),
				("Pipeline shell load", await self.test_unified_pipeline_loading(page)),
				("Image upload", await self.test_enhanced_file_upload(page, image_files)),
				("Pipeline execution", await self.test_complete_pipeline_execution(page)),
				("3D viewer", await self.test_enhanced_3d_model_viewer(page)),
				("Real-data validation", await self.test_real_data_validation(page)),
				("UI interactions", await self.test_comprehensive_ui_interactions(page)),
			]

			await browser.close()

		passed = sum(1 for _, ok in results_matrix if ok)
		total = len(results_matrix)

		print("\n================ SUMMARY ================" )
		for label, ok in results_matrix:
			print(f"   {label:<25} {'✅' if ok else '❌'}")
		print(f"Overall: {passed}/{total} checks passed ({passed/total:.0%})")

		overall_success = passed / total >= 0.85
		self.test_results["suite_summary"] = {
			"results": {label: ok for label, ok in results_matrix},
			"passed": passed,
			"total": total,
			"overall_success": overall_success,
		}

		if overall_success:
			print("🎉 Enhanced pipeline validation passed")
		else:
			print("⚠️ Enhanced pipeline validation incomplete")

		if server_started_here:
			await self.stop_server()

		return overall_success

	def save_enhanced_results(self) -> None:
		"""Persist the structured test results for downstream reporting."""

		results_file = self.project_root / "ENHANCED_PLAYWRIGHT_TEST_RESULTS.json"
		self.test_results.setdefault("metadata", {})
		self.test_results["metadata"].update(
			{
				"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
				"base_url": self.base_url,
				"pipeline_url": self.pipeline_url,
				"screenshot_directory": str(self.screenshot_dir),
				"images_directory": str(self.test_images_dir),
			}
		)

		with results_file.open("w", encoding="utf-8") as handle:
			json.dump(self.test_results, handle, indent=2)

		print(f"📄 Results written to {results_file}")


async def main() -> int:
	print("🚀 Launching enhanced comprehensive Playwright test")
	tester = Enhanced4DPipelinePlaywrightTest()
	success = await tester.run_comprehensive_test()
	tester.save_enhanced_results()
	return 0 if success else 1


if __name__ == "__main__":
	raise SystemExit(asyncio.run(main()))
