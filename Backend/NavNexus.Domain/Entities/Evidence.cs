namespace NavNexus.Domain.Entities;

public class Evidence
    {
        public string Id { get; set; }                   // unique evidence ID
        public string SourceId { get; set; }             // ID document gốc
        public string SourceName { get; set; }           // tên file gốc
        public string ChunkId { get; set; }              // ID chunk liên quan
        public string Text { get; set; }                 // nội dung evidence
        public int Page { get; set; }                    // trang trong document
        public float Confidence { get; set; }            // độ tin cậy
        public DateTime CreatedAt { get; set; }          // thời gian tạo
        public string Language { get; set; }   = "ENG"  ;       // ngôn ngữ
        public string SourceLanguage { get; set; }  = "ENG"  ;     // ngôn ngữ gốc
        public string HierarchyPath { get; set; } = String.Empty;       // đường dẫn trong tài liệu

        public List<string> Concepts { get; set; } = new List<string>(); // danh sách concepts

        public List<string> KeyClaims { get; set; } = new List<string>(); // các claim quan trọng
        public List<string> QuestionsRaised { get; set; } = new List<string>(); // câu hỏi liên quan
        public float EvidenceStrength { get; set; }      // độ tin cậy của node

        public Evidence()
        {
            Id = Guid.NewGuid().ToString();
            SourceId = string.Empty;
            SourceName = string.Empty;
            ChunkId = string.Empty;
            Text = string.Empty;
            Page = 0;
            Confidence = 0.0f;
            CreatedAt = DateTime.UtcNow;
            Language = "ENG";
            SourceLanguage = "ENG";
            HierarchyPath = string.Empty;
            EvidenceStrength = 0.0f;
        }
    }
