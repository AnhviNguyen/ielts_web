# LinguaIELTS — Google Form Feedback

Script tự tạo biểu mẫu khảo sát phản hồi người dùng cho đồ án (§4.2 User Feedback).

## Cách cài (5 phút)

1. Mở [Google Apps Script](https://script.google.com) → **New project**
2. Xóa code mặc định, dán nội dung file `linguaielts-feedback-form.gs`
3. Sửa dòng đầu:
   ```javascript
   const NOTIFY_EMAIL = 'email-cua-ban@vku.edu.vn';
   ```
4. Chọn hàm **`createFeedbackForm`** → **Run** → Authorize quyền (Form, Sheet, Gmail nếu dùng email)
5. **View → Logs** → copy link **Form** gửi người dùng
6. Chọn hàm **`installSubmitTrigger`** → **Run** (một lần)

## Hàm có sẵn

| Hàm | Mục đích |
|-----|----------|
| `createFeedbackForm` | Tạo Form + Sheet mới (chạy 1 lần) |
| `installSubmitTrigger` | Bật email + tóm tắt khi có phản hồi |
| `showFormLinks` | In lại link Form/Sheet |
| `buildAnalysisSheet` | Tạo tab Analysis với điểm TB Likert |

## Gửi cho người dùng thử

```
Bạn vui lòng:
1. Đăng ký và dùng thử https://[URL-WEB-CỦA-BẠN]
2. Thử ít nhất: 1 kỹ năng R/L + 1 W hoặc S + xem Dashboard
3. Điền form feedback (~5 phút): [LINK GOOGLE FORM]
```

## Ghi vào báo cáo

Sau khi có ≥20 phản hồi, chạy `buildAnalysisSheet` → copy bảng **Analysis** vào Word (Table 28).

**Hạn chế nên ghi trong báo cáo:** mẫu pilot nhỏ, không có nhóm đối chứng, điểm AI chỉ formative.
