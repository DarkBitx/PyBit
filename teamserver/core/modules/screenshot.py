from PIL import ImageGrab
import io

def main():
    image = ImageGrab.grab()
    buffer = io.BytesIO()

    image.save(buffer, format="PNG")

    buffer.seek(0)

    header = "SCREENSHOT"
    result = buffer.getvalue()
    return header,result

