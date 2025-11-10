from flask import Flask, render_template, request, redirect
import redis

app = Flask(__name__)

r = redis.Redis(
    host="fraud-cache-gecd9x.serverless.apse2.cache.amazonaws.com",
    port=6379,
    ssl=True
)

@app.route("/")
def home():
    # Lấy danh sách blacklist
    blacklist = [item.decode() for item in r.smembers("blacklist:nameOrig")]
    return render_template("index.html", blacklist=blacklist)

@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name")
    if name:
        r.sadd("blacklist:nameOrig", name)
    return redirect("/")

@app.route("/delete/<name>")
def delete(name):
    r.srem("blacklist:nameOrig", name)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)