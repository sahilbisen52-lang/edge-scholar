"""
CLI Workflow for Qualcomm AI Hub Integration in EdgeScholar.

Run with:
    python scripts/qualcomm_ai_hub_workflow.py --list
    python scripts/qualcomm_ai_hub_workflow.py --generate-script llama-v3_2-3b-instruct
"""
from __future__ import annotations

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.qualcomm_ai_hub import QualcommAIHubManager, QUALCOMM_AI_HUB_CATALOG
from app.utils.paths import get_models_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="EdgeScholar Qualcomm AI Hub Workflow Utility")
    parser.add_argument("--list", action="store_true", help="List all curated Qualcomm AI Hub models")
    parser.add_argument("--generate-script", type=str, metavar="MODEL_ID", help="Generate qai_hub compilation script")
    parser.add_argument("--target-device", type=str, default="Snapdragon X Elite CRD", help="Target device preset")
    args = parser.parse_args()

    manager = QualcommAIHubManager(get_models_dir())

    print("=" * 70)
    print("  EdgeScholar — Qualcomm AI Hub Workflow")
    print("=" * 70)

    sdk_status = "INSTALLED ✅" if manager.is_hub_sdk_installed() else "Not Installed (Install with: pip install qai-hub)"
    print(f"Qualcomm AI Hub SDK (qai_hub): {sdk_status}\n")

    if args.generate_script:
        model = manager.get_model(args.generate_script)
        if not model:
            print(f"❌ Model '{args.generate_script}' not found in catalog.")
            sys.exit(1)
        script_code = manager.generate_hub_compile_script(args.generate_script, args.target_device)
        out_file = f"compile_{args.generate_script}.py"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(script_code)
        print(f"Generated compilation script for '{model.display_name}':")
        print(f"Saved to: {out_file}\n")
        print("Script contents preview:")
        print("-" * 50)
        print(script_code)
        print("-" * 50)
        return

    # Default: List models
    print(f"{'Model Name':<32} | {'Precision':<10} | {'Runtime Target':<22}")
    print("-" * 70)
    for m in manager.list_curated_models():
        deploy = manager.check_local_deployment(m.model_id)
        status_tag = " [DEPLOYED]" if deploy["deployed"] else ""
        print(f"{m.display_name[:32]:<32} | {m.precision:<10} | {m.runtime[:22]:<22}{status_tag}")
        print(f"  └─ Hub URL: {m.hub_url}")
        print(f"  └─ Use Case: {m.use_case}\n")

    print("=" * 70)
    print("To generate a compilation script for Qualcomm AI Hub cloud compilation:")
    print("  python scripts/qualcomm_ai_hub_workflow.py --generate-script llama-v3_2-3b-instruct")


if __name__ == "__main__":
    main()
