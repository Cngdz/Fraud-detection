# PayShield - Real-time AI-powered Financial Fraud Detection System

![Architecture]

## Tổng quan

**PayShield** là hệ thống phát hiện và ngăn chặn gian lận giao dịch tài chính theo thời gian thực, được triển khai trên nền tảng AWS serverless.  
Hệ thống được thiết kế để:

- Bảo vệ khách hàng và Core Banking khỏi các giao dịch gian lận.
- Tăng tốc xử lý giao dịch hợp lệ.
- Cung cấp dashboard để admin quản lý và giám sát các giao dịch đáng ngờ.

Hệ thống chạy song song theo 2 luồng chính:

1. **Luồng Nóng (Hot Path)**:  
   - Check rule in-memory nhanh (<200ms) bằng Redis/ElastiCache.  
   - Trả kết quả Approved/Declined tức thì.  
   - Push dữ liệu sang Kinesis để Luồng Lạnh xử lý.
   - Lưu các giao dịch không hợp lệ vào S3

2. **Luồng Lạnh (Cold Path)**:  
   - Đọc dữ liệu từ Kinesis.  
   - Gọi SageMaker Endpoint để chấm điểm AI cho giao dịch.  
   - Lưu kết quả vào DynamoDB phục vụ cho xây dựng dashboard.  
   - Nếu phát hiện gian lận, gửi alert qua SNS tới External System.

## Kiến trúc & Công nghệ chính

- **API Gateway**: Nhận request giao dịch từ External System.
- **Lambda Functions**: Xử lý Hot Path, Cold Path và Alert.
- **ElastiCache (Redis)**: Lưu trữ rules để check siêu nhanh.
- **AWS Kinesis**: Luồng dữ liệu giữa Hot Path và Cold Path.
- **AWS S3**: Lưu trữ log thô và kết quả AI cho compliance.
- **AWS DynamoDB**: Lưu trữ kết quả AI để tra cứu nhanh.
- **Amazon SageMaker Endpoint**: Chạy mô hình AI phân tích gian lận.
- **AWS SNS**: Gửi cảnh báo đến admin hoặc hệ thống ngoài.
- **OpenSearch Dashboards**: Dashboard theo thời gian thực cho admin.