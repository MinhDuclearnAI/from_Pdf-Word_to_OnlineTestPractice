import fitz

def test_pymupdf():
    # Use a dummy pdf to test if we can get image blocks
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello World before image")
    # Insert a dummy image
    pix = fitz.Pixmap(fitz.csRGB, (0, 0, 100, 100), False)
    pix.clear_with(255)
    page.insert_image(fitz.Rect(50, 60, 150, 160), pixmap=pix)
    page.insert_text((50, 180), "Hello World after image")

    blocks = page.get_text("blocks", sort=True)
    for b in blocks:
        print(b)
    
if __name__ == "__main__":
    test_pymupdf()
