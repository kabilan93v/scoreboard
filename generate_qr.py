import qrcode
import os

def generate_qr():
    # Update this URL to your hosted viewer page (like Render, Replit, etc.)
    public_url = "https://scoreboard-wxtx.onrender.com/viewer"

    # Ensure 'static' directory exists
    if not os.path.exists("static"):
        os.makedirs("static")

    # Save the QR code image to static/qr.png
    qr_path = os.path.join("static", "qr.png")
    img = qrcode.make(public_url)
    img.save(qr_path)
    print(f"QR code saved to {qr_path}")

if __name__ == "__main__":
    generate_qr()
