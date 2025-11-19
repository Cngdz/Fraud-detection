from flask import Flask, render_template, request, redirect
import redis

app = Flask(__name__)

# Kết nối Redis Serverless AWS
r = redis.Redis(
    host="fraud-redis-gecd9x.serverless.apse2.cache.amazonaws.com",
    port=6379,
    ssl=True
)

# ----------------------------------------------------
# Helper: SCAN (do Redis Serverless không hỗ trợ KEYS)
# ----------------------------------------------------
def scan_keys(pattern):
    cursor = 0
    results = []
    while True:
        cursor, keys = r.scan(cursor=cursor, match=pattern)
        results.extend(keys)
        if cursor == 0:
            break
    return results


# ----------------------------------------------------
# Trang chủ: danh sách tất cả blacklist keys
# ----------------------------------------------------
@app.route("/")
def home():
    raw_keys = scan_keys("blacklist:*")
    keys = [k.decode().replace("blacklist:", "") for k in raw_keys]
    return render_template("home.html", keys=keys)


# ----------------------------------------------------
# Tạo key mới
# ----------------------------------------------------
@app.route("/add_key", methods=["POST"])
def add_key():
    key = request.form.get("key")
    if key:
        redis_key = f"blacklist:{key}"
        # thêm metadata để giữ key luôn tồn tại
        r.sadd(redis_key, "__meta__")
    return redirect("/")


# ----------------------------------------------------
# Xem bên trong một key
# ----------------------------------------------------
@app.route("/key/<key>")
def view_key(key):
    redis_key = f"blacklist:{key}"
    items = [i.decode() for i in r.smembers(redis_key) if i.decode() != "__meta__"]
    return render_template("key_detail.html", key=key, items=items)


# ----------------------------------------------------
# Thêm item vào key
# ----------------------------------------------------
@app.route("/key/<key>/add", methods=["POST"])
def add_item(key):
    item = request.form.get("item")
    if item:
        r.sadd(f"blacklist:{key}", item)
    return redirect(f"/key/{key}")


# ----------------------------------------------------
# Xoá item khỏi key
# ----------------------------------------------------
@app.route("/key/<key>/delete/<item>")
def delete_item(key, item):
    r.srem(f"blacklist:{key}", item)
    return redirect(f"/key/{key}")


# ----------------------------------------------------
# Chạy app Flask
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
