from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Ciao, questo è il mio primo server Flask!"

if __name__ == "__main__":
    app.run(share=True)