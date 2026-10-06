"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": "Delegate to this subagent to inspect the workspace, read files, analyze data samples, and report factual observations without modifying any files.",
            "system_prompt": "You are an explorer subagent. Your role is to examine files and data structures, discover conventions, and report your findings accurately without making any modifications.",
        },
        {
            "name": "implementer",
            "description": "Delegate to this subagent to write or edit code, process data files, execute scripts, and implement required fixes or output files.",
            "system_prompt": "You are an implementer subagent. Your role is to write clean code, clean and process data, edit files, and run commands to carry out the implementation tasks.",
        },
        {
            "name": "reviewer",
            "description": "Delegate to this subagent to independently inspect the final output files, verify data accuracy, and test edge cases before finishing.",
            "system_prompt": "You are a reviewer subagent. Your role is to check output files and code against requirements and edge cases, reporting any issues found without modifying files.",
        },
    ]
