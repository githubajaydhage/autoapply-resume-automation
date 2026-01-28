#!/usr/bin/env python3
"""Clean up temporary files and prepare for commit."""

import os
import subprocess
import sys

os.chdir('/workspaces/autoapply-resume-automation')

# Remove temporary files
files_to_remove = [
    'push_workflow.py',
    'push_workflow.sh'
]

print("🧹 Cleaning up temporary files...\n")

for file in files_to_remove:
    if os.path.exists(file):
        os.remove(file)
        print(f"  ✅ Removed: {file}")
    else:
        print(f"  ⏭️  Already removed: {file}")

print("\n" + "="*60)
print("GIT STATUS AFTER CLEANUP")
print("="*60)

# Show git status
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
print(result.stdout if result.stdout else "Clean working directory")

print("\n✅ Cleanup complete!")
