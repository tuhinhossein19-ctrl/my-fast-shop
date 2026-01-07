# my-fast-shop
from flask import Flask, render_template_string, request, jsonify
import requests
import threading
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = "mega_pro_instant_save"

# কনফিগারেশন
TELEGRAM_TOKEN = "8102849425:AAE-MnmDwJ-zHde8uaM6NM7isNWXkBT4sYs"
CHAT_ID = "7482867864"

def get_db():
    return sqlite3.connect('pro_orders.db')

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, 
                 address TEXT, items TEXT, total TEXT, payment TEXT, time TEXT)''')
init_db()

# ১০০টি প্রোডাক্ট জেনারেশন
product_list = [
    {"name": "প্রিমিয়াম কলম", "icon": "pen"}, {"name": "নোটবুক", "icon": "book"},
    {"name": "ইরেজার", "icon": "eraser"}, {"name": "পেন্সিল", "icon": "pencil"},
    {"name": "মার্কার", "icon": "marker"}, {"name": "শার্পনার", "icon": "sharpener"},
    {"name": "স্কেল", "icon": "ruler"}, {"name": "স্ট্যাপলার", "icon": "stapler"},
    {"name": "ক্যালকুলেটর", "icon": "calculator"}, {"name": "ব্যাগ", "icon": "backpack"}
]

products = []
for i in range(100):
    item = product_list[i % len(product_list)]
    products.append({
        "id": i + 1,
        "name": f"{item['name']} { (i // len(product_list)) + 1 }",
        "price": random.randint(20, 1200),
        "image": f"https://img.icons8.com/fluency/200/{item['icon']}.png"
    })

CLIENT_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mega Stationery Shop</title>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root { --main: #6c5ce7; --bg: #f8f9fc; }
        body { margin:0; font-family: 'Hind Siliguri', sans-serif; background: var(--bg); }
        .navbar { background: white; padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; position: sticky; top:0; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        .search-box { width: 100%; max-width: 400px; padding: 10px 15px; border: 1px solid #ddd; border-radius: 25px; outline: none; }
        .container { max-width: 1200px; margin: 20px auto; padding: 0 15px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 20px; padding: 20px; text-align: center; border: 1px solid #eee; }
        .card img { width: 80px; height: 80px; margin-bottom: 15px; }
        .btn { background: var(--main); color: white; border: none; padding: 12px; border-radius: 12px; cursor: pointer; width: 100%; font-weight: bold; }
        .cart-bar { background: white; padding: 20px; border-radius: 20px 20px 0 0; position: fixed; bottom: 0; left: 0; right: 0; z-index: 999; display: none; box-shadow: 0 -5px 25px rgba(0,0,0,0.1); }
        #order-form-page { display: none; position: fixed; inset: 0; background: white; z-index: 2000; padding: 30px; overflow-y: auto; }
        .form-box { max-width: 450px; margin: 0 auto; }
        input, textarea, select { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 10px; box-sizing: border-box; font-family: inherit; }
        #receipt-modal { display:none; position:fixed; inset:0; background:white; z-index:4000; padding:20px; text-align: center; }
    </style>
</head>
<body>

<div class="navbar">
    <div style="font-size:20px; font-weight:bold; color:var(--main);">🖋️ মেগা শপ</div>
    <input type="text" class="search-box" id="search-input" placeholder="পণ্য খুঁজুন..." onkeyup="filterProducts()">
    <div style="cursor:pointer; background:#eee; padding:8px 15px; border-radius:20px;">🛒 ৳ <span id="total-top">0</span></div>
</div>

<div class="container">
    <div class="grid" id="product-grid">
        {% for p in products %}
        <div class="card" data-name="{{ p.name }}">
            <img src="{{ p.image }}">
            <h3 style="font-size:18px; margin:10px 0;">{{ p.name }}</h3>
            <div style="color:var(--main); font-weight:bold; font-size:20px;">৳ {{ p.price }}</div>
            <button class="btn" onclick="addToCart({{ p.id }}, '{{ p.name }}', {{ p.price }})">অ্যাড করুন</button>
        </div>
        {% endfor %}
    </div>
</div>

<div id="cart-bar" class="cart-bar">
    <h3 style="margin:0">🛍️ শপিং ব্যাগ</h3>
    <div id="cart-items-list" style="margin:10px 0;"></div>
    <button class="btn" onclick="goToForm()">অর্ডার নিশ্চিত করুন</button>
</div>

<div id="order-form-page">
    <div class="form-box">
        <button onclick="document.getElementById('order-form-page').style.display='none'" style="border:none; background:none; color:var(--main); cursor:pointer; font-weight:bold;">⬅ পেছনে যান</button>
        <h2 style="text-align:center">অর্ডার ফরম</h2>
        <input type="text" id="cust-name" placeholder="আপনার নাম">
        <input type="tel" id="cust-phone" placeholder="মোবাইল নম্বর">
        <textarea id="cust-addr" placeholder="পুরো ঠিকানা"></textarea>
        <select id="payment-method">
            <option value="Cash on Delivery">ক্যাশ অন ডেলিভারি</option>
            <option value="bKash">বিকাশ</option>
        </select>
        <button class="btn" onclick="finalCheckout()" id="confirm-btn">অর্ডার সম্পন্ন করুন</button>
    </div>
</div>

<div id="receipt-modal">
    <div style="border:2px solid #eee; padding:30px; border-radius:20px; display:inline-block; width:100%; max-width:400px; margin-top:50px;">
        <h2 style="color:var(--main);">অর্ডার সফল হয়েছে! ✅</h2>
        <p>আইডি: #<span id="r-id"></span></p>
        <h3 id="r-total" style="background:var(--main); color:white; padding:10px; border-radius:10px;"></h3>
        <button class="btn" onclick="location.reload()">হোমপেজে ফিরুন</button>
    </div>
</div>

<script>
    let cart = {};

    function filterProducts() {
        let input = document.getElementById('search-input').value.toLowerCase();
        let cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            let name = card.getAttribute('data-name').toLowerCase();
            card.style.display = name.includes(input) ? "block" : "none";
        });
    }

    function addToCart(id, name, price) {
        if(cart[id]) cart[id].qty++; else cart[id] = {name, price, qty: 1};
        updateUI();
        document.getElementById('cart-bar').style.display = 'block';
    }

    function updateUI() {
        let total = 0;
        let list = document.getElementById('cart-items-list');
        list.innerHTML = "";
        Object.values(cart).forEach(i => {
            total += i.price * i.qty;
            list.innerHTML += `<div>${i.name} x ${i.qty}</div>`;
        });
        document.getElementById('total-top').innerText = total;
    }

    function goToForm() { document.getElementById('order-form-page').style.display = 'block'; }

    async function finalCheckout() {
        const n = document.getElementById('cust-name').value;
        const p = document.getElementById('cust-phone').value;
        const a = document.getElementById('cust-addr').value;
        const pm = document.getElementById('payment-method').value;

        if(!n || !p || !a) return alert("দয়া করে সব তথ্য পূরণ করুন!");

        document.getElementById('confirm-btn').innerText = "প্রসেস হচ্ছে...";
        document.getElementById('confirm-btn').disabled = true;

        let oid = Math.floor(100000 + Math.random() * 900000);
        let items = Object.values(cart).map(i => `${i.name}(${i.qty})`).join(", ");
        let total = document.getElementById('total-top').innerText;

        const response = await fetch('/api/order', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({n, p, a, items, total, pm, oid})
        });

        if(response.ok) {
            document.getElementById('r-id').innerText = oid;
            document.getElementById('r-total').innerText = "মোট বিল: ৳" + total;
            document.getElementById('receipt-modal').style.display = 'block';
            document.getElementById('order-form-page').style.display = 'none';
        }
    }
</script>
</body>
</html>
"""

# ইনবক্স পেজ
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Inbox</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f4; padding: 20px; }
        table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        th { background: #6c5ce7; color: white; }
        tr:nth-child(even) { background: #f9f9f9; }
    </style>
</head>
<body>
    <h2>📥 অর্ডার ইনবক্স (সরাসরি জমা)</h2>
    <table>
        <tr><th>ID</th><th>Customer</th><th>Phone</th><th>Items</th><th>Total</th><th>Payment</th><th>Time</th></tr>
        {% for row in orders %}
        <tr><td>#{{ loop.index }}</td><td>{{ row[1] }}<br><small>{{ row[3] }}</small></td><td>{{ row[2] }}</td><td>{{ row[4] }}</td><td>৳{{ row[5] }}</td><td>{{ row[6] }}</td><td>{{ row[7] }}</td></tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(CLIENT_HTML, products=products)

@app.route("/admin")
def admin():
    with get_db() as conn:
        orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    return render_template_string(ADMIN_HTML, orders=orders)

@app.route("/api/order", methods=['POST'])
def place_order():
    d = request.json
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    with get_db() as conn:
        conn.execute("INSERT INTO orders (name, phone, address, items, total, payment, time) VALUES (?,?,?,?,?,?,?)",
                     (d['n'], d['p'], d['a'], d['items'], d['total'], d['pm'], now))
    
    def notify():
        try:
            text = f"🛎️ নতুন অর্ডার!\n👤 {d['n']}\n📞 {d['p']}\n🏠 {d['a']}\n🛒 {d['items']}\n💰 ৳{d['total']}\n💳 {d['pm']}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text}, timeout=2)
        except: pass

    threading.Thread(target=notify).start()
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
