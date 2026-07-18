import sys
import platform

print("=== Environment Verification ===")
print(f"Python Version: {sys.version}")
print(f"Platform: {platform.platform()}")

required_libs = ["pandas", "numpy", "matplotlib", "requests"]
missing_libs = []

for lib in required_libs:
    try:
        __import__(lib)
        print(f"[OK] {lib} is installed.")
    except ImportError:
        print(f"[MISSING] {lib} is NOT installed.")
        missing_libs.append(lib)

if missing_libs:
    print(f"\nPlease install the missing libraries: pip install {' '.join(missing_libs)}")
    sys.exit(1)
else:
    print("\nAll verified libraries are present!")
    sys.exit(0)
