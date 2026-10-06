# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Hải Long | 2A202602471 | 100% |

- Mô hình (tên deployment hoặc `LAB_MODEL`), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `openai/gpt-4o-mini` (OpenRouter OpenAI-compatible gateway), `LAB_TEMPERATURE=0`, `recursion_limit=50`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents 0.7.21`, Windows, chạy trực tiếp (local venv)
- Số lần chạy tác vụ đã dùng / ngân sách: 6 / 20
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

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `data-learn` | `rule_money_in_cents` | E. Vi phạm quy ước tổ chức | `RULE: money values in answer.json are integer cents (1606.67 USD is written 160667).` |
| `data-learn` | `rule_meta_block` | E. Vi phạm quy ước tổ chức | `RULE: answer.json has an object meta = {"source": <input file name>, "rows_in": <rows>, "rows_used": <rows>}.` |
| `data-learn` | `rule_clean_csv` | E. Vi phạm quy ước tổ chức | `RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents...` |
| `data-learn` | `north_q1_revenue` | D. Bỏ sót dữ liệu bẩn hoặc định dạng | `north_q1_revenue: wrong value (got 443.34)` (chưa chuẩn hóa đa định dạng ngày DD/MM/YYYY, YYYY-MM-DD và offset UTC trước khi lọc Q1). |
| `data-learn` | `missing_amount_orders` | D. Bỏ sót dữ liệu bẩn hoặc định dạng | `missing_amount_orders: wrong value (got 4)` (bỏ sót giá trị sentinel `-999` đại diện cho amount bị thiếu theo README). |
| `code-learn` | `tests_not_modified` | A. Bỏ qua đặc tả | `the original files in tests/ must not be modified (new test files are allowed)` (tác tử sửa thẳng vào file test có sẵn thay vì sửa code trong `inventory/`). |
| `code-learn` | `parse_price_all_formats` | D. Bỏ sót dữ liệu bẩn hoặc định dạng | `wrong for: ['(12.00)']` (chưa xử lý format số âm đặt trong ngoặc đơn kế toán `(12.00)`). |
| `code-learn` | `other_caller_fixed` | B. Không kiểm chứng | `SyntaxError: f-string expression part cannot include a backslash (export.py, line 12)` (tác tử kết thúc mà không chạy lại test suite để kiểm tra cú pháp). |
| `code-learn` | `rule_regression_tests` | E. Vi phạm quy ước tổ chức | `RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass.` |
| `code-learn` | `rule_changelog` | E. Vi phạm quy ước tổ chức | `RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>'.` |
| `logs-learn` | `valid_structure` | B. Không kiểm chứng | `JSONDecodeError: Expecting ',' delimiter: line 1 column 41183 (char 41182)` (file json lớn bị lỗi cú pháp nhưng tác tử không chạy lệnh python để parse validate lại). |
| `logs-learn` | `rule_service_names` | E. Vi phạm quy ước tổ chức | Check `rule_` thất bại do quy ước chuẩn hóa tên service không có trong mô tả đề bài ban đầu. |
| `logs-learn` | `rule_sorted_errors` | E. Vi phạm quy ước tổ chức | Check `rule_` thất bại do quy ước sắp xếp thứ tự lỗi theo thời gian là quy ước nội bộ của Acme. |

**Nhận xét:**
- **Nhóm lỗi chiếm đa số:** Nhóm E (Vi phạm quy ước tổ chức) chiếm đa số tuyệt đối (0/9 check quy ước đạt ở baseline), tiếp theo là Nhóm D (Bỏ sót định dạng/dữ liệu bẩn) và Nhóm B (Không chạy lệnh kiểm chứng trước khi kết thúc).
- **Nguyên nhân chung:** Mô hình baseline chưa từng được tiếp cận các quy ước nội bộ không văn bản hóa của Acme (`house-rules`). Đối với các lỗi kỹ thuật (A-D), tác tử vội vã kết thúc mà không tận dụng công cụ `execute` để chạy kiểm tra chéo (sanity checks/linter/parser).
- **Bằng chứng phủ định:** Theo `python scripts/check_breakdown.py`, tác tử baseline đạt 2/18 check kỹ thuật (`discount_rounds_half_up` trong `code-learn` và `top_region` trong `data-learn`), chứng tỏ mô hình có năng lực hiểu bài toán cơ bản nhưng thiếu thông tin quy ước.
- **Khả năng phòng ngừa của Skill:** Kỹ năng (Skill) hoàn toàn có thể phòng ngừa triệt để nhóm E và nhóm D bằng cách tài liệu hóa các quy ước (meta block, clean.csv, format cents, changelog, regression tests, format ngày/timezone) vào `skills/auto/`, giúp tác tử nạp vào context ngay từ bước đầu tiên (`SKILLS_NOTE`).

## 5. Điều kiện `subagents` (Phần 2.3)

- **Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):**
  + `explorer`: Chuyên khảo sát cấu trúc tệp, đọc docstring, README và mẫu dữ liệu bẩn; báo cáo sự thật khách quan, không sửa đổi file. Thiết kế nhằm tránh làm ô nhiễm không gian làm việc trong giai đoạn tìm hiểu.
  + `implementer`: Chuyên thực hiện chỉnh sửa mã nguồn, viết script lọc dữ liệu, sửa lỗi và chạy lệnh shell. Thiết kế để tập trung vào logic thực thi.
  + `reviewer`: Chuyên độc lập đối chiếu kết quả đầu ra với đề bài, kiểm tra tính hợp lệ của file JSON/CSV và các trường hợp biên. Thiết kế nhằm khắc phục nhóm lỗi B (Không kiểm chứng).
- **`subagent_calls` ở từng tác vụ và nhận xét (kể cả trường hợp bằng 0):**
  + `code-learn`: `subagent_calls = 0` (tác tử chính tự trực tiếp đọc file và gọi lệnh sửa).
  + `data-learn`: `subagent_calls = 1` (tác tử chính nhận thấy tác vụ phân tích dữ liệu phức tạp nên đã ủy quyền cho subagent qua công cụ `task`).
  + `logs-learn`: `subagent_calls = 0` (tác tử chính tự mình xử lý đọc và phân tích file log).
  + *Nhận xét:* Việc `subagent_calls = 0` ở 2 tác vụ là hoàn toàn bình thường và hợp lệ; tác tử chính tự chủ quyết định chỉ ủy quyền khi tác vụ có khối lượng tính toán/phân tích lớn (`data-learn`).
- **Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc):**
  + Ở `data-learn`, prompt giao việc của tác tử chính rất chi tiết (nêu rõ các cột, điều kiện lọc Q1, xử lý -999, các khóa cần xuất). Tuy nhiên, thông tin về các quy ước ẩn của Acme (`rule_money_in_cents`, `rule_clean_csv`, `rule_meta_block`) vẫn bị thiếu vì bản thân tác tử chính lúc này chưa biết các quy ước này.
- **Ảnh hưởng đến token và thời gian:**
  + **Token:** Trung bình tiêu thụ ở điều kiện `subagents` là **64,700 tokens**, tăng khoảng **49.1%** so với `baseline` (**43,379 tokens**). Sự gia tăng chủ yếu đến từ `data-learn` (146,297 tokens so với 40,471 tokens) do chi phí ngữ cảnh khi khởi tạo và trao đổi với subagent.
  + **Thời gian & Hiệu quả:** Ở `code-learn`, tác tử trong điều kiện subagents đạt kết quả tốt hơn (**2/10 check đạt**, 20.0s, 21,887 tokens) so với baseline (**1/10 check đạt**, 44.7s, 46,279 tokens) do hệ thống prompt phân quyền giúp tác tử định hướng hành động dứt khoát hơn.

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
