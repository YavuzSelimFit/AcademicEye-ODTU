import os
import sys

print(f"User Home: {os.path.expanduser('~')}")
print(f"Scopus Config Path Should Be: {os.path.join(os.path.expanduser('~'), '.scopus', 'config.ini')}")

target = os.path.join(os.path.expanduser('~'), '.scopus', 'config.ini')
if os.path.exists(target):
    print("✅ File Exists via os.path")
else:
    print("❌ File DOES NOT EXIST via os.path")

try:
    import pybliometrics
    print(f"Pybliometrics Version: {pybliometrics.__version__}")
    # Try to find where it looks
    from pybliometrics.scopus.utils import constants
    print(f"Constants CONFIG_FILE: {constants.CONFIG_FILE}")
except Exception as e:
    print(f"Error importing: {e}")
