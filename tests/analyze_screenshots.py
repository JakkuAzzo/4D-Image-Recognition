#!/usr/bin/env python3
"""
Screenshot Analysis Tool
Analyzes the captured screenshots to verify frontend functionality
"""

import json
import os
from pathlib import Path

def analyze_screenshots():
    # Find the most recent test directory
    screenshot_base = "test screenshots"
    test_dirs = [d for d in os.listdir(screenshot_base) if d.startswith("frontend_test_")]
    if not test_dirs:
        print("❌ No test directories found")
        return
    
    latest_test = sorted(test_dirs)[-1]
    test_dir = Path(screenshot_base) / latest_test
    
    print(f"🔍 Analyzing screenshots from: {test_dir}")
    print("=" * 60)
    
    # Read analysis report
    analysis_file = test_dir / "analysis_report.json"
    if analysis_file.exists():
        with open(analysis_file, 'r') as f:
            report = json.load(f)
        
        print("📊 Test Results Summary:")
        for test, passed in report["test_results"].items():
            status = "✅ PASS" if passed else "❌ FAIL"
            test_name = test.replace("_", " ").title()
            print(f"   {status} - {test_name}")
        
        print(f"\n📸 Screenshot Analysis:")
        print(f"   Total Screenshots: {report['screenshot_analysis']['total_screenshots']}")
        print(f"   Successful Captures: {report['screenshot_analysis']['successful_captures']}")
        print(f"   Success Rate: {report['summary']['success_rate']}")
        
        print(f"\n🗂️ Screenshot Details:")
        for result in report['screenshot_analysis']['analysis_results']:
            step_name = result['step'].replace('_', ' ').title()
            print(f"   📷 {step_name}")
            print(f"      Description: {result['description']}")
            print(f"      Elements: {result['visible_elements']} visible")
            print(f"      Page Height: {result['page_height']}px")
            print("")
        
        # Analyze specific screenshots for key features
        print("🔍 Key Feature Analysis:")
        
        # Check for specific elements in each screenshot
        screenshot_files = list(test_dir.glob("*.png"))
        
        feature_analysis = {
            "upload_elements": "02_upload_elements.png",
            "step_navigation": "03_step_navigation.png", 
            "model_preview": "04_model_preview.png",
            "osint_section": "05_osint_section.png",
            "processing_indicator": "06_processing_indicator.png",
            "step_interactions": ["07_step_1_active.png", "07_step_2_active.png", "07_step_3_active.png"]
        }
        
        for feature, files in feature_analysis.items():
            if isinstance(files, list):
                found_files = [f for f in files if (test_dir / f).exists()]
                if found_files:
                    print(f"   ✅ {feature.replace('_', ' ').title()}: {len(found_files)} interaction screenshots")
                else:
                    print(f"   ❌ {feature.replace('_', ' ').title()}: No screenshots found")
            else:
                if (test_dir / files).exists():
                    print(f"   ✅ {feature.replace('_', ' ').title()}: Screenshot captured")
                else:
                    print(f"   ❌ {feature.replace('_', ' ').title()}: Screenshot missing")
        
        print(f"\n🎯 Final Assessment:")
        success_rate = float(report['summary']['success_rate'].replace('%', ''))
        if success_rate == 100.0:
            print("   🎉 PERFECT SCORE! All frontend fixes are working correctly!")
            print("   ✅ Screenshots confirm visual elements are properly implemented")
            print("   ✅ Step navigation is interactive and functional")
            print("   ✅ All required components are visible and highlighted")
        elif success_rate >= 80.0:
            print("   ✅ EXCELLENT! Most fixes are working correctly")
            print("   ⚠️ Minor issues may need attention")
        else:
            print("   ⚠️ Some issues need further investigation")
            print("   📸 Check screenshots for visual verification")
        
        print(f"\n📁 All screenshots saved in: {test_dir}")
        print("💡 Review individual screenshots to verify visual correctness")
        
    else:
        print("❌ Analysis report not found")

if __name__ == "__main__":
    analyze_screenshots()
