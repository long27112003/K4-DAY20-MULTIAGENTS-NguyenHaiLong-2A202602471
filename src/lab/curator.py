"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import logging
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


CURATOR_PROMPT_TEMPLATE = """You are an expert developer and prompt engineer designing procedural skills for an agent doing coding and data analysis tasks.
Below are the failed checks (check names and grading bot feedback) and recent execution traces from task runs.
Analyze the procedural errors and organizational rules (e.g. house rules starting with RULE:) that were violated.
Synthesize up to {max_skills} short, general-purpose procedural skills to prevent these failures on new tasks of the same type.

Rules for each skill:
- Generalize: Do NOT include task-specific IDs, filenames of a single task, specific numbers, or solutions.
- Do include general organizational rules (e.g., standard metadata schema, regression tests requirement, changelog format, cleaning CSV standards, money representation).
- Each skill must start with YAML frontmatter:
  name: <lowercase-hyphenated-name> (max 64 chars)
  description: <Use when ... (one concise sentence describing the triggering situation)>
- Body must be concise (under 50 lines), actionable checklist / procedural steps.
- Format each skill EXACTLY as follows:
=== SKILL: <name> ===
---
name: <name>
description: <when to use>
---
<actionable checklist body>
=== END ===

Failed runs:
{runs_section}
"""


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    results_path = Path(results_dir)
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    else:
        out_dir = Path(out_dir)

    runs = []
    cond_dir = results_path / source_condition
    if cond_dir.exists():
        for run_file in sorted(cond_dir.glob("*/run.json")):
            try:
                data = json.loads(run_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            # Tuyệt đối bỏ qua tác vụ đánh giá
            if data.get("role") != "learn":
                continue

            failed = [
                {"name": c.get("name", ""), "detail": c.get("detail", "")}
                for c in data.get("checks", [])
                if not c.get("passed", False)
            ]

            trace_file = run_file.parent / "trace.md"
            trace_snippet = ""
            if trace_file.exists():
                try:
                    trace_text = trace_file.read_text(encoding="utf-8")
                    trace_snippet = trace_text[-3000:]
                except Exception:
                    pass

            runs.append({
                "task": data.get("task", run_file.parent.name),
                "failed": failed,
                "trace": trace_snippet,
            })

    if not any(r["failed"] for r in runs):
        print("Cảnh báo: không có check thất bại ở tác vụ học trong source_condition =", source_condition)
        return []

    runs_blocks = []
    for r in runs:
        if not r["failed"]:
            continue
        task_str = f"Task: {r['task']}\nFailed checks:"
        failed_lines = [f"- {f['name']}: {f['detail']}" for f in r["failed"]]
        block = task_str + "\n" + "\n".join(failed_lines)
        if r["trace"]:
            block += f"\nRecent trace snippet:\n{r['trace']}"
        runs_blocks.append(block)

    runs_section = "\n\n".join(runs_blocks)
    prompt = CURATOR_PROMPT_TEMPLATE.format(max_skills=max_skills, runs_section=runs_section)

    if model is None:
        model = make_model()

    response = model.invoke(prompt, max_tokens=2500)
    reply_text = response.content if hasattr(response, "content") else str(response)

    blocks = parse_skill_blocks(reply_text)
    written = []

    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            continue

        skill_dir = out_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(text, encoding="utf-8")
        written.append(skill_path)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
