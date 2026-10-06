# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Hải Long | 2A202602471 | 100% |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `deepseek/deepseek-chat` (OpenRouter OpenAI-compatible gateway), `LAB_TEMPERATURE=0`, `recursion_limit=50`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents 0.7.21`, Windows, chạy trực tiếp (local venv)
- Số lần chạy tác vụ đã dùng / ngân sách: 0 / 20
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

> Dự đoán điều kiện nào đạt điểm cao nhất trên **tác vụ đánh giá** và vì sao. Nêu căn cứ từ phân loại lỗi (mục 4) và từ tài liệu tham khảo. Điền cả ba dòng; `verify_freeze.py` kiểm tra điều này.

- H1 (subagents so với baseline):
- H2 (skills-auto so với baseline):
- H3 (tác vụ học so với tác vụ đánh giá):

## 3. Làm quen Deep Agents (Phần 0.3)

### Câu 1: Bài lab này có bao nhiêu agent? Mỗi agent làm gì?
Hệ thống trong lab gồm **1 tác tử chính (Coordinator)** và **3 tác tử con (Worker Subagents)** (cùng một tác tử Curator phục vụ tự tiến hóa ở giai đoạn sau):
- **Coordinator (Main Agent):** Tiếp nhận yêu cầu đề bài từ harness, nắm quyền điều phối tổng thể toàn bộ quá trình giải quyết bài toán. Coordinator phân tích vấn đề, có thể tự xử lý hoặc phân rã công việc và ủy quyền (dispatch) cho các worker subagents thông qua công cụ `task`, sau đó tổng hợp báo cáo và nghiệm thu kết quả cuối cùng.
- **Worker Agent 1 (`explorer`):** Chuyên trách nghiên cứu và khảo sát. Khám phá không gian làm việc (`workspace/`), đọc hiểu các file đề bài, docstring, kiểm tra mẫu dữ liệu bẩn và báo cáo trung thực sự thật cho Coordinator mà không trực tiếp sửa đổi file.
- **Worker Agent 2 (`implementer`):** Chuyên trách thực hiện và sửa đổi. Viết script xử lý dữ liệu, tái cấu trúc mã nguồn, sửa lỗi bug theo hướng dẫn và chạy lệnh shell/tests để xác nhận thay đổi.
- **Worker Agent 3 (`reviewer` / Evaluator):** Đánh giá độc lập chất lượng đầu ra sau khi `implementer` hoàn thành. Kiểm tra chéo kết quả với quy ước đề bài và các trường hợp biên (edge cases), chạy check kiểm tra chất lượng trước khi nộp.
*(Bên cạnh đó, **Curator Agent** là tác tử tiến hóa chạy độc lập sau các lần chạy để đọc log/trace thất bại và tự động sinh ra các skill tối ưu vào `skills/auto/`).*

### Câu 2: Coordinator giao tiếp với worker agents bằng cách nào?
Coordinator giao tiếp với các Worker Agents thông qua **công cụ `task` (Tool Call mechanism)** do Deep Agents cung cấp:
- **Giao việc:** Coordinator gọi công cụ `task(subagent_type="...", prompt="...")` kèm mô tả chi tiết nhiệm vụ, ngữ cảnh cần thiết và định dạng kết quả mong đợi.
- **Cô lập ngữ cảnh (Context Isolation):** Mỗi lần gọi là một phiên bản (instance) độc lập, không tự động kế thừa lịch sử hội thoại của Coordinator. Subagent chỉ nhìn thấy prompt được giao và tự vận hành suy luận/gọi công cụ riêng.
- **Trả kết quả:** Worker agent hoàn thành nhiệm vụ và trả về kết quả dưới dạng **một báo cáo cuối duy nhất (final report)** thông qua `ToolMessage` cho Coordinator.
- **Phản hồi và điều phối tiếp:** Coordinator đọc báo cáo kết quả, xác minh (verify) và quyết định gán việc tiếp theo cho agent khác hoặc tự hoàn tất tác vụ.

### Câu 3: Có những công cụ (tools) nào được chia sẻ giữa các agent?
Các agent cùng chia sẻ chung một môi trường thực thi (`LocalShellBackend`) trên không gian sandbox với các nhóm công cụ:
- **Nhóm công cụ thao tác tệp ảo (Virtual File Tools):** `ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`. Tất cả các agent đều dùng chung các công cụ này để tương tác với cây thư mục trong sandbox.
- **Nhóm công cụ thực thi lệnh shell:** `execute` cho phép chạy các lệnh bash/python trong sandbox một cách an toàn (cô lập biến môi trường nhạy cảm, chỉ kế thừa PATH cần thiết).
- **Quy ước đường dẫn chung:** Cả Coordinator và các Subagents đều được tiêm quy ước `PATHS_NOTE` để thống nhất sử dụng đường dẫn tương đối (`workspace/...`, `skills/...`).
- **Kho tri thức và kỹ năng chung (Skills):** Các kỹ năng trong thư mục `skills/` (chẳng hạn do Curator tự sinh) có thể được nạp và chia sẻ để các agent cùng tham chiếu và áp dụng.
*(Lưu ý: Riêng công cụ `task` chỉ được cấp cho Coordinator để điều phối, worker subagents thường không gọi đệ quy công cụ này).*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

> Chỉ dùng tác vụ học. Mỗi dòng là một check thất bại.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| | | | |

Nhận xét: nhóm lỗi nào chiếm đa số? Skill có thể phòng ngừa nhóm đó không?

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
- `subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0):
- Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc):
- Ảnh hưởng đến token và thời gian:

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do:

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| | | | |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
