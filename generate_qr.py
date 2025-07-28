import qrcode

public_url = "https://scoreboard-wxtx.onrender.com/viewer"
img = qrcode.make(public_url)
img.save("static/qr.png")
