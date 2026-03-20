from flask import Flask, render_template, request
from alert_service import send_alert

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("alert.html")


@app.route("/alert")
def alert():

    accident_type = request.args.get("type")
    location = request.args.get("location")
    message = request.args.get("message")

    full_message = f"{accident_type} detected at {location}. {message}"

    send_alert(full_message)

    return "Alert sent"

if __name__ == "__main__":
    app.run(port=5050, debug=True)
