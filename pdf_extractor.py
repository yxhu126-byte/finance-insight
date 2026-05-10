import fitz  # PyMuPDF

def extract_text(pdf_path: str, max_pages: int = None) -> str:
    """从 PDF 中提取全部文本。"""
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        pages_to_read = min(len(doc), max_pages) if max_pages else len(doc)

        for i in range(pages_to_read):
            page = doc[i]
            full_text += page.get_text()
            full_text += "\n--- PAGE_BREAK ---\n"

        doc.close()
        return full_text
    except Exception as e:
        print(f"PDF解析失败: {e}")
        return ""


def get_metadata(pdf_path: str) -> dict:
    """提取文档元数据（文件名、页数）"""
    try:
        doc = fitz.open(pdf_path)
        metadata = {
            "filename": pdf_path,
            "page_count": len(doc),
            "title": doc.metadata.get("title", pdf_path),
        }
        doc.close()
        return metadata
    except Exception:
        return {"filename": pdf_path, "page_count": 0, "title": pdf_path}
