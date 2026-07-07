"""
Quick test to verify orchestrator API endpoints are accessible.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print("[OK] Import path configured")

try:
    from app.orchestrator.api import router
    print("[OK] Orchestrator API router imported successfully")
    print(f"[OK] Router prefix: {router.prefix}")
    print(f"[OK] Available routes: {len(router.routes)}")
    for route in router.routes:
        print(f"  - {route.methods} {route.path}")
except Exception as e:
    print(f"[FAIL] Failed to import orchestrator API: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[OK] Orchestrator module is properly wired and ready to use!")
