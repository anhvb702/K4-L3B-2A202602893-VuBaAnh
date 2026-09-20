# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Bá Anh
**Nhóm:** G16
**Ngày:** 20/9/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau, thường biểu diễn hai văn bản có nội dung hoặc ý nghĩa gần nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Khách hàng có thể đổi sản phẩm trong vòng 7 ngày."
- Câu B: "Người mua được phép đổi hàng trong thời hạn một tuần."
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng cùng diễn đạt chính sách đổi hàng trong 7 ngày.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Khách hàng có thể đổi sản phẩm trong vòng 7 ngày."
- Câu B: "Máy chủ cần được sao lưu vào mỗi đêm."
- Tại sao khác: Hai câu nói về hai chủ đề không liên quan.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
Cosine tập trung vào hướng của vector nên ít bị ảnh hưởng bởi độ dài văn bản. Điều này phù hợp với text embedding hơn khoảng cách Euclid, vốn dễ tăng chỉ vì một văn bản có nhiều token hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
* Trình bày phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23`.
* Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
Với overlap bằng 100, công thức cho `ceil((10000 - 100) / (500 - 100)) = 25` chunks. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới chunk tốt hơn, nhưng làm tăng số chunk và chi phí embedding/tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**Chiến lược chunk riêng — `HeadingChunker`:**
Tôi tách Markdown tại các dòng heading (`#` đến `######`) để giữ mỗi mục chính sách như một đơn vị ngữ nghĩa. Nếu section dài hơn giới hạn, tôi dùng recursive chunking cho phần thân và gắn lại heading vào từng chunk con để không mất ngữ cảnh.

**`SentenceChunker.chunk`** — hướng tiếp cận:
Tôi dùng regex tách sau các dấu `.`, `!`, hoặc `?` khi phía sau là khoảng trắng hoặc hết chuỗi: `(?<=[.!?])(?:\s+|$)`. Cách này giữ lại dấu câu, loại khoảng trắng dư thừa và trả về danh sách rỗng với text rỗng. Chữ viết tắt như `TS.` và số thập phân vẫn có thể bị tách sai.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
Thuật toán thử các separator theo thứ tự ưu tiên, gom các mảnh liền kề cho tới khi gần `chunk_size`, rồi đệ quy những mảnh còn quá dài với separator tiếp theo. Base case là mảnh đã đủ ngắn, hết separator, hoặc phải cắt cứng theo `chunk_size` khi không còn ranh giới phù hợp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
Mỗi `Document` được chuẩn hóa thành record gồm id, content, metadata và embedding; metadata được copy để không làm thay đổi dữ liệu đầu vào. Khi tìm kiếm, embedding của query được so sánh với từng record bằng cosine similarity và sắp xếp giảm dần theo score.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
`search_with_filter` lọc metadata trước rồi mới tính similarity trên tập ứng viên còn lại, tránh việc các kết quả không phù hợp chiếm hết top-k. `delete_document` xóa mọi record có id hoặc `metadata["doc_id"]` trùng document cần xóa và trả về trạng thái thành công.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
`answer` truy xuất top-k chunk, đánh số từng chunk và đưa source cùng nội dung vào prompt. Prompt yêu cầu chỉ dùng context được cung cấp, nói rõ khi thiếu thông tin và trích dẫn số chunk liên quan; nếu store rỗng, agent trả thông báo trực tiếp.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
```text
============================= test session starts =============================
collected 42 items

42 passed in 0.11s
```

Môi trường đã được tạo trong `.venv` và dependency trong `requirements.txt` đã được cài đặt.
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể đổi sản phẩm trong vòng 7 ngày. | Người mua được phép đổi hàng trong thời hạn một tuần. | cao | -0.0240 | Không theo ngữ nghĩa; mock embedding cho kết quả âm |
| 2 | Khách hàng có thể đổi sản phẩm trong vòng 7 ngày. | Máy chủ cần được sao lưu vào mỗi đêm. | thấp | -0.1045 | Có, thấp |
| 3 | Chính sách bảo hành áp dụng cho sản phẩm lỗi. | Sản phẩm bị lỗi được hưởng chế độ bảo hành. | cao | 0.0508 | Có nhưng score thấp |
| 4 | Người bán phải cung cấp thông tin bảo hành. | Người mua cần tìm hiểu thời tiết ngày mai. | thấp | -0.0198 | Không đáng tin do mock embedding |
| 5 | Thời hạn bảo hành là 12 tháng. | Sản phẩm có màu xanh dương. | thấp | 0.0481 | Không, score dương dù khác nghĩa |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
Kết quả bất ngờ nhất là cặp 1 có cùng ý nghĩa nhưng score âm `-0.0240`, trong khi cặp 5 không liên quan lại có score dương `0.0481`. Điều này cho thấy mock embedding chỉ băm MD5 để tạo vector giả, không biểu diễn ý nghĩa ngôn ngữ; cosine score ở đây chỉ kiểm tra pipeline toán học, không dùng để kết luận semantic similarity.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn người mua gửi yêu cầu trả hàng là bao lâu? | 15 ngày dương lịch sau khi đơn chuyển sang Đã giao hàng. | return-refund-policy#0, 0.7212 | Có | Agent trả lời được thời hạn 15 ngày từ context [1]. |
| 2 | Người bán phải thực hiện bảo hành theo thông tin nào? | Theo chính sách và thời hạn đã niêm yết khi đăng sản phẩm. | seller-warranty-listing#0, 0.6944 | Có | Agent trả lời được phải theo thông tin bảo hành đã niêm yết. |
| 3 | TikTok hỗ trợ người mua khi người bán từ chối bảo hành thế nào? | Hỗ trợ trong phạm vi có thể để sản phẩm được xử lý đúng chính sách. | buyer-warranty-support#0, 0.7891 | Có | Agent trả lời được TikTok hỗ trợ trong phạm vi có thể. |
| 4 | Người bán cần khai báo thông tin bảo hành nào khi đăng sản phẩm? | Thời hạn và chính sách bảo hành cùng các điều khoản cần cung cấp cho người mua. | seller-warranty-listing#0, 0.7458 | Có | Agent trả lời được cần khai báo thời hạn và chính sách bảo hành. |
| 5 | Có những hình thức bảo hành nào cho hàng đã qua sử dụng? | Quốc tế, nhà sản xuất, nhà cung cấp hoặc không bảo hành. | refurbished-warranty#0, 0.6662 | Có | Agent liệt kê được 4 hình thức bảo hành từ context [1]. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**; cả 5 câu đều có chunk đúng ở top-1 khi dùng `text-embedding-3-small`.

**Nguồn tham khảo cho bộ câu hỏi:**

- TikTok Shop, [Khi nào người mua có thể đưa ra yêu cầu trả hàng/hoàn tiền?](https://seller-vn.tiktok.com/university/essay?knowledge_id=2901402355762946&lang=vi-VN), audience: buyer, truy cập 20/09/2026.
- TikTok Shop, [Trả hàng và Hoàn tiền](https://seller-vn.tiktok.com/university/essay?course_type=1&from=search&identity=1&knowledge_id=1766935302801169&role=1), audience: seller, truy cập 20/09/2026.
- TikTok Shop, [Quản lý yêu cầu chỉ hoàn tiền](https://seller-vn.tiktok.com/university/essay?knowledge_id=4924096304482065&lang=vi-VN), audience: seller, truy cập 20/09/2026.
- Shopee, [Những điều cần biết về Trả hàng do “Đổi ý/không còn nhu cầu”](https://help.shopee.vn/portal/4/article/204305-Nh%E1%BB%AFng-%C4%91i%E1%BB%81u-c%E1%BA%A7n-bi%E1%BA%BFt-v%E1%BB%81-Tr%E1%BA%A3-h%C3%A0ng-do-%22%C4%90%E1%BB%95i-%C3%BD%2Fkh%C3%B4ng-c%C3%B2n-nhu-c%E1%BA%A7u%22?previousPage=search+results+page), audience: buyer, truy cập 20/09/2026.
- TikTok Shop, [Chính sách hủy đơn hàng, trả hàng và hoàn tiền của khách hàng](https://seller-vn.tiktok.com/university/essay?article_type=agreement&default_language=en&knowledge_id=6837773789234946), audience: seller, truy cập 20/09/2026.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
Từ benchmark, metadata filter giúp loại tài liệu sai đối tượng và giữ đúng corpus buyer/seller. So với mock embedding, `text-embedding-3-small` đưa chunk đúng lên top-1 cho cả 5 câu hỏi, với score từ 0.6662 đến 0.7891. Các chunk cùng chủ đề vẫn có score gần nhau, nên metadata và heading cần được giữ để tăng khả năng truy vết.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 3 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **56 / 60** |
