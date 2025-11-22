# Chunking với Position Tracking

## Tổng quan

Module chunking đã được nâng cấp để theo dõi **vị trí chính xác** của mỗi chunk trong văn bản gốc. Điều này cho phép truy vết ngược lại nguồn gốc của evidence và cải thiện khả năng kiểm chứng.

## Các trường mới trong Chunk

Mỗi chunk hiện có các trường sau:

```python
{
    "index": 0,                    # Số thứ tự chunk
    "text": "...",                 # Nội dung text
    "start_pos": 0,                # Vị trí ký tự bắt đầu trong văn bản gốc
    "end_pos": 296,                # Vị trí ký tự kết thúc trong văn bản gốc
    "overlap_previous": "...",      # Text overlap với chunk trước
    "has_more": True               # Có chunk tiếp theo không
}
```

## Sử dụng cơ bản

```python
from src.pipeline.chunking import create_smart_chunks

text = "Văn bản dài của bạn..."
chunks = create_smart_chunks(text, chunk_size=2000, overlap=400)

for chunk in chunks:
    print(f"Chunk {chunk['index']}: [{chunk['start_pos']}:{chunk['end_pos']}]")
    print(f"Text: {chunk['text'][:100]}...")
```

## Tạo Evidence với Position

```python
def create_evidence_with_position(document, chunk):
    """Tạo evidence object với thông tin vị trí đầy đủ"""
    return {
        "evidence_id": f"{document['id']}_CHUNK_{chunk['index']}",
        "document_id": document["id"],
        "document_title": document["title"],

        # Nội dung text
        "text": chunk["text"],

        # Thông tin vị trí - QUAN TRỌNG
        "position": {
            "start_char": chunk["start_pos"],
            "end_char": chunk["end_pos"],
            "length": len(chunk["text"])
        },

        # Metadata
        "chunk_metadata": {
            "chunk_index": chunk["index"],
            "has_more": chunk["has_more"]
        }
    }
```

## Trích xuất văn bản gốc từ Position

```python
# Lấy lại văn bản gốc từ document dựa vào position
def extract_original_text(document_text, evidence):
    start = evidence["position"]["start_char"]
    end = evidence["position"]["end_char"]
    return document_text[start:end]

# Sử dụng
original_text = extract_original_text(document["content"], evidence)
print(original_text)
```

## Use Cases

### 1. Source Tracing - Truy vết nguồn gốc
```python
def highlight_in_document(document_text, evidence):
    """Highlight text trong document viewer"""
    start = evidence["position"]["start_char"]
    end = evidence["position"]["end_char"]

    # Có thể dùng để highlight trong PDF, web viewer, etc.
    return {
        "text": document_text[start:end],
        "start": start,
        "end": end,
        "page": calculate_page_number(start)  # Nếu có thông tin page
    }
```

### 2. Verification - Kiểm chứng
```python
def verify_evidence_integrity(document_text, evidence):
    """Kiểm tra evidence có bị thay đổi không"""
    start = evidence["position"]["start_char"]
    end = evidence["position"]["end_char"]

    original = document_text[start:end]
    current = evidence["text"]

    return original.strip() in current or current in original
```

### 3. Analytics - Phân tích
```python
def analyze_document_coverage(document_text, evidences):
    """Phân tích phần nào của document được sử dụng nhiều nhất"""
    usage_map = [0] * len(document_text)

    for evidence in evidences:
        start = evidence["position"]["start_char"]
        end = evidence["position"]["end_char"]

        for i in range(start, end):
            usage_map[i] += 1

    return usage_map
```

### 4. Linking - Liên kết evidences
```python
def find_overlapping_evidences(evidence1, evidence2):
    """Tìm evidences có vùng text chồng lấn"""
    start1 = evidence1["position"]["start_char"]
    end1 = evidence1["position"]["end_char"]
    start2 = evidence2["position"]["start_char"]
    end2 = evidence2["position"]["end_char"]

    # Kiểm tra overlap
    overlap = max(0, min(end1, end2) - max(start1, start2))

    return {
        "has_overlap": overlap > 0,
        "overlap_chars": overlap,
        "overlap_percentage": (overlap / min(end1-start1, end2-start2)) * 100
    }
```

### 5. Incremental Update - Cập nhật tăng dần
```python
def update_affected_chunks(document_text, old_text, change_position, change_length):
    """Chỉ cập nhật các chunks bị ảnh hưởng khi document thay đổi"""
    affected_chunks = []

    for evidence in all_evidences:
        start = evidence["position"]["start_char"]
        end = evidence["position"]["end_char"]

        # Chunk bị ảnh hưởng nếu position nằm trong vùng thay đổi
        if start <= change_position <= end or start <= (change_position + change_length) <= end:
            affected_chunks.append(evidence)

    return affected_chunks
```

## Lưu vào Neo4j

```python
def save_evidence_to_neo4j(tx, evidence):
    """Lưu evidence với position vào Neo4j"""
    query = """
    CREATE (e:Evidence {
        id: $evidence_id,
        text: $text,
        start_pos: $start_pos,
        end_pos: $end_pos,
        chunk_index: $chunk_index
    })
    RETURN e
    """

    tx.run(query,
        evidence_id=evidence["evidence_id"],
        text=evidence["text"],
        start_pos=evidence["position"]["start_char"],
        end_pos=evidence["position"]["end_char"],
        chunk_index=evidence["chunk_metadata"]["chunk_index"]
    )
```

## Truy vấn trong Neo4j

```cypher
// Tìm evidences trong một vùng text cụ thể
MATCH (e:Evidence)
WHERE e.start_pos >= 100 AND e.end_pos <= 500
RETURN e

// Tìm evidences overlap với một vùng
MATCH (e:Evidence)
WHERE e.start_pos <= 500 AND e.end_pos >= 100
RETURN e

// Tìm evidence gần nhất với một vị trí
MATCH (e:Evidence)
RETURN e, abs(e.start_pos - 300) as distance
ORDER BY distance
LIMIT 1
```

## Best Practices

1. **Luôn lưu position**: Khi tạo evidence, luôn lưu `start_pos` và `end_pos`
2. **Kiểm chứng định kỳ**: Định kỳ verify evidence với document gốc
3. **Index position**: Tạo index trên `start_pos`, `end_pos` trong database để query nhanh
4. **Track document version**: Lưu version của document để biết position tương ứng với version nào
5. **Handle edge cases**: Xử lý trường hợp document thay đổi, position không còn hợp lệ

## Testing

Xem các file test để biết thêm chi tiết:
- `test_chunking_positions.py` - Test cơ bản về position tracking
- `example_evidence_with_positions.py` - Ví dụ đầy đủ về evidence structure

## Ví dụ Output

```json
{
  "evidence_id": "DOC_2024_001_CHUNK_0",
  "text": "Tổng quan kinh tế...",
  "position": {
    "start_char": 0,
    "end_char": 296,
    "length": 296
  }
}
```

## Lợi ích

✅ Truy vết chính xác nguồn gốc evidence
✅ Kiểm chứng tính toàn vẹn của dữ liệu
✅ Highlight text trong document viewer
✅ Phân tích usage patterns
✅ Tối ưu caching và incremental updates
✅ Link và merge evidences hiệu quả
