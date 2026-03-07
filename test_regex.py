import re

tests = [
    "main",
    "cacc7f16",
    "student_vs_teacher/cacc7f16_vs_4f2a1b9c",
    "origin/student_vs_teacher/cacc7f16_vs_4f2a1b9c",
    "feature/my-branch",
    "cacc7f1",
    "student_vs_teacher/cacc7f16",
    ""
]

for current_branch in tests:
    is_valid_branch = False
    if current_branch == "main":
        is_valid_branch = True
    elif re.match(r"^[a-fA-F0-9]{8}$", current_branch):
        is_valid_branch = True
    elif re.match(r"^(origin/)?student_vs_teacher/[a-fA-F0-9]{8}_vs_[a-fA-F0-9]{8}$", current_branch):
        is_valid_branch = True
        
    print(f"{current_branch}: {is_valid_branch}")
