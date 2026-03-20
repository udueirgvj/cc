from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import sqlite3, hashlib, os, uuid, json, random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'WittenWeb_Secret_2025!'
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'wittenweb.db')

ADMIN_PASSWORD   = 'Ww@Admin#9X2mK!47'
FINANCE_PASSWORD = 'Ww$Finance!8Tz3#Qp'

# ══════════════════════════════════════════
#  قاعدة البيانات
# ══════════════════════════════════════════
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id               TEXT PRIMARY KEY,
            first_name       TEXT NOT NULL,
            last_name        TEXT NOT NULL,
            email            TEXT UNIQUE NOT NULL,
            password         TEXT NOT NULL,
            two_fa           TEXT NOT NULL,
            platform_balance REAL    DEFAULT 0,
            seller_rating    REAL    DEFAULT 4.5,
            admin_rating     INTEGER DEFAULT 0,
            is_imposter      INTEGER DEFAULT 0,
            purchase_count   INTEGER DEFAULT 0,
            total_spent      REAL    DEFAULT 0,
            created_at       TEXT
        );

        CREATE TABLE IF NOT EXISTS products (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            price       REAL NOT NULL,
            description TEXT,
            category    TEXT DEFAULT "classic",
            emoji       TEXT DEFAULT "👔",
            color       TEXT DEFAULT "#1a1a1a",
            seller_id   TEXT,
            seller_name TEXT,
            rating      REAL DEFAULT 4.5,
            reviews     INTEGER DEFAULT 0,
            image       TEXT,
            created_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS notes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            note         TEXT,
            from_user    TEXT,
            time         TEXT
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id          TEXT PRIMARY KEY,
            buyer_id    TEXT,
            buyer_name  TEXT,
            total       REAL,
            status      TEXT DEFAULT "pending",
            items       TEXT,
            time        TEXT
        );

        CREATE TABLE IF NOT EXISTS logs (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            uid    TEXT,
            action TEXT,
            type   TEXT,
            time   TEXT
        );

        CREATE TABLE IF NOT EXISTS finance (
            key   TEXT PRIMARY KEY,
            value REAL DEFAULT 0
        );
    ''')
    c.execute("INSERT OR IGNORE INTO finance VALUES ('balance',  0)")
    c.execute("INSERT OR IGNORE INTO finance VALUES ('total_in', 0)")
    c.execute("INSERT OR IGNORE INTO finance VALUES ('total_out',0)")
    conn.commit()
    conn.close()

def h(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def now():
    return datetime.now().isoformat()

# ══════════════════════════════════════════
#  صفحات
# ══════════════════════════════════════════
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/finance')
def finance():
    return render_template('finance.html')

# ══════════════════════════════════════════
#  مستخدمون
# ══════════════════════════════════════════
@app.route('/api/register', methods=['POST'])
def register():
    d = request.get_json()
    first = d.get('firstName','').strip()
    last  = d.get('lastName','').strip()
    email = d.get('email','').strip().lower()
    pw    = d.get('password','')

    if not all([first, last, email, pw]):
        return jsonify({'error': 'أدخل جميع الحقول'}), 400
    if len(pw) < 8:
        return jsonify({'error': 'كلمة المرور أقل من 8 أحرف'}), 400

    db = get_db()
    if db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone():
        db.close()
        return jsonify({'error': 'البريد مسجل مسبقاً'}), 400

    uid   = 'WW-' + str(uuid.uuid4()).upper()[:8]
    twofa = str(random.randint(100000, 999999))

    db.execute(
        'INSERT INTO users (id,first_name,last_name,email,password,two_fa,created_at) VALUES (?,?,?,?,?,?,?)',
        (uid, first, last, email, h(pw), twofa, now())
    )
    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        (uid, f'تسجيل حساب جديد — {first} {last}', 'register', now()))
    db.commit()
    db.close()
    return jsonify({'success': True, 'uid': uid, 'twoFA': twofa, 'name': first})


@app.route('/api/login', methods=['POST'])
def login():
    d     = request.get_json()
    email = d.get('email','').strip().lower()
    pw    = d.get('password','')
    code  = d.get('twoFA','')

    db   = get_db()
    user = db.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()

    if not user or user['password'] != h(pw):
        db.close()
        return jsonify({'error': 'البريد أو كلمة المرور غير صحيحة'}), 401

    if not code:
        # مرحلة 1 — أرسل كود 2FA
        db.close()
        return jsonify({'step': 2, 'twoFA': user['two_fa']})

    if code != user['two_fa']:
        db.close()
        return jsonify({'error': 'كود التحقق غير صحيح'}), 401

    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        (user['id'], 'تسجيل دخول', 'login', now()))
    db.commit()
    u = dict(user)
    db.close()
    return jsonify({'success': True, 'user': u})


@app.route('/api/users', methods=['GET'])
def get_users():
    db = get_db()
    rows = db.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/users/<uid>', methods=['GET'])
def get_user(uid):
    db   = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    db.close()
    if not user:
        return jsonify({'error': 'غير موجود'}), 404
    return jsonify(dict(user))


@app.route('/api/users/<uid>', methods=['DELETE'])
def delete_user(uid):
    db = get_db()
    db.execute('DELETE FROM users WHERE id=?', (uid,))
    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        (uid, 'حذف الحساب', 'admin', now()))
    db.commit()
    db.close()
    return jsonify({'success': True})


@app.route('/api/users/<uid>/rating', methods=['POST'])
def set_rating(uid):
    rating = request.get_json().get('rating', 0)
    db = get_db()
    db.execute('UPDATE users SET admin_rating=? WHERE id=?', (rating, uid))
    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        (uid, f'تقييم مشرف: {rating} نجوم حمراء', 'admin', now()))
    db.commit()
    db.close()
    return jsonify({'success': True})


@app.route('/api/users/<uid>/imposter', methods=['POST'])
def toggle_imposter(uid):
    db   = get_db()
    user = db.execute('SELECT is_imposter FROM users WHERE id=?', (uid,)).fetchone()
    nv   = 0 if user['is_imposter'] else 1
    db.execute('UPDATE users SET is_imposter=? WHERE id=?', (nv, uid))
    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        (uid, 'تفعيل علامة الانتحال' if nv else 'إلغاء علامة الانتحال', 'admin', now()))
    db.commit()
    db.close()
    return jsonify({'success': True, 'is_imposter': nv})


@app.route('/api/users/<uid>/zero', methods=['POST'])
def zero_user_balance(uid):
    db   = get_db()
    user = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    if not user:
        db.close()
        return jsonify({'error': 'غير موجود'}), 404
    bal = user['platform_balance']
    db.execute('UPDATE users SET platform_balance=0 WHERE id=?', (uid,))
    db.execute('UPDATE finance SET value=value+? WHERE key="balance"',  (bal,))
    db.execute('UPDATE finance SET value=value+? WHERE key="total_in"', (bal,))
    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        (uid, f'تصفير رصيد ${bal:.2f} → حساب الدفع', 'transfer', now()))
    db.commit()
    db.close()
    return jsonify({'success': True, 'transferred': bal})

# ══════════════════════════════════════════
#  منتجات
# ══════════════════════════════════════════
@app.route('/api/products', methods=['GET'])
def get_products():
    db   = get_db()
    rows = db.execute('SELECT * FROM products ORDER BY created_at DESC').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/products', methods=['POST'])
def add_product():
    d   = request.get_json()
    pid = 'UP-' + str(uuid.uuid4()).upper()[:8]
    db  = get_db()
    db.execute(
        '''INSERT INTO products
           (id,name,price,description,category,emoji,color,seller_id,seller_name,image,created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        (pid, d['name'], float(d['price']), d.get('description',''),
         d.get('category','classic'), d.get('emoji','👔'), d.get('color','#1a1a1a'),
         d.get('seller_id',''), d.get('seller_name',''),
         d.get('image',''), now())
    )
    db.commit()
    db.close()
    return jsonify({'success': True, 'id': pid})


@app.route('/api/products/<pid>', methods=['DELETE'])
def delete_product(pid):
    db = get_db()
    db.execute('DELETE FROM products WHERE id=?', (pid,))
    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        ('admin', f'حذف منتج {pid}', 'admin', now()))
    db.commit()
    db.close()
    return jsonify({'success': True})

# ══════════════════════════════════════════
#  الدفع
# ══════════════════════════════════════════
@app.route('/api/checkout', methods=['POST'])
def checkout():
    d       = request.get_json()
    buyer   = d.get('buyer_id','')
    items   = d.get('items', [])
    total   = float(d.get('total', 0))
    tx_id   = 'TX-' + str(uuid.uuid4()).upper()[:10]

    db = get_db()
    # سجّل العملية
    db.execute(
        'INSERT INTO transactions (id,buyer_id,buyer_name,total,status,items,time) VALUES (?,?,?,?,?,?,?)',
        (tx_id, buyer, d.get('buyer_name',''), total, 'pending',
         json.dumps(items, ensure_ascii=False), now())
    )
    # المال → حساب الدفع أولاً (ليس التاجر)
    db.execute('UPDATE finance SET value=value+? WHERE key="balance"',  (total,))
    db.execute('UPDATE finance SET value=value+? WHERE key="total_in"', (total,))
    # تحديث بيانات المشتري
    db.execute(
        'UPDATE users SET purchase_count=purchase_count+1, total_spent=total_spent+? WHERE id=?',
        (total, buyer)
    )
    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        (buyer, f'شراء بقيمة ${total:.2f} — {tx_id}', 'purchase', now()))
    db.commit()
    db.close()
    return jsonify({'success': True, 'tx_id': tx_id})

# ══════════════════════════════════════════
#  ملاحظات
# ══════════════════════════════════════════
@app.route('/api/notes', methods=['GET'])
def get_notes():
    db   = get_db()
    rows = db.execute('SELECT * FROM notes ORDER BY id DESC').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/notes', methods=['POST'])
def add_note():
    d  = request.get_json()
    db = get_db()
    db.execute(
        'INSERT INTO notes (product_name,note,from_user,time) VALUES (?,?,?,?)',
        (d.get('product',''), d.get('note',''), d.get('from','زائر'), now())
    )
    db.commit()
    db.close()
    return jsonify({'success': True})

# ══════════════════════════════════════════
#  سجل الأنشطة
# ══════════════════════════════════════════
@app.route('/api/logs', methods=['GET'])
def get_logs():
    db   = get_db()
    rows = db.execute('SELECT * FROM logs ORDER BY id DESC').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/logs', methods=['DELETE'])
def clear_logs():
    db = get_db()
    db.execute('DELETE FROM logs')
    db.commit()
    db.close()
    return jsonify({'success': True})

# ══════════════════════════════════════════
#  حساب الدفع
# ══════════════════════════════════════════
@app.route('/api/finance', methods=['GET'])
def get_finance():
    db   = get_db()
    rows = db.execute('SELECT * FROM finance').fetchall()
    db.close()
    return jsonify({r['key']: r['value'] for r in rows})


@app.route('/api/finance/transfer', methods=['POST'])
def finance_transfer():
    d       = request.get_json()
    from_id = d.get('from','')
    to_id   = d.get('to','')
    amount  = float(d.get('amount', 0))

    if amount <= 0:
        return jsonify({'error': 'المبلغ غير صحيح'}), 400

    db = get_db()
    if from_id == 'MAIN':
        bal = db.execute('SELECT value FROM finance WHERE key="balance"').fetchone()['value']
        if bal < amount:
            db.close()
            return jsonify({'error': 'رصيد حساب الدفع غير كافٍ'}), 400
        db.execute('UPDATE finance SET value=value-? WHERE key="balance"',   (amount,))
        db.execute('UPDATE finance SET value=value+? WHERE key="total_out"', (amount,))
        db.execute('UPDATE users SET platform_balance=platform_balance+? WHERE id=?', (amount, to_id))
    else:
        user = db.execute('SELECT platform_balance FROM users WHERE id=?', (from_id,)).fetchone()
        if not user or user['platform_balance'] < amount:
            db.close()
            return jsonify({'error': 'رصيد المرسِل غير كافٍ'}), 400
        db.execute('UPDATE users SET platform_balance=platform_balance-? WHERE id=?', (amount, from_id))
        db.execute('UPDATE users SET platform_balance=platform_balance+? WHERE id=?', (amount, to_id))

    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        (from_id, f'تحويل ${amount:.2f} من {from_id} إلى {to_id}', 'transfer', now()))
    db.commit()
    db.close()
    return jsonify({'success': True})


@app.route('/api/finance/add', methods=['POST'])
def finance_add():
    d      = request.get_json()
    uid    = d.get('uid','')
    amount = float(d.get('amount', 0))
    db     = get_db()
    if uid == 'MAIN':
        db.execute('UPDATE finance SET value=value+? WHERE key="balance"',  (amount,))
        db.execute('UPDATE finance SET value=value+? WHERE key="total_in"', (amount,))
    else:
        db.execute('UPDATE users SET platform_balance=platform_balance+? WHERE id=?', (amount, uid))
    db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
        (uid, f'إضافة رصيد ${amount:.2f}', 'finance', now()))
    db.commit()
    db.close()
    return jsonify({'success': True})


@app.route('/api/finance/zero', methods=['POST'])
def finance_zero():
    d   = request.get_json()
    uid = d.get('uid','')
    db  = get_db()
    if uid == 'MAIN':
        bal = db.execute('SELECT value FROM finance WHERE key="balance"').fetchone()['value']
        db.execute('UPDATE finance SET value=value+? WHERE key="total_out"', (bal,))
        db.execute('UPDATE finance SET value=0 WHERE key="balance"')
        db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
            ('MAIN', f'تصفير حساب الدفع ${bal:.2f}', 'finance', now()))
    else:
        user = db.execute('SELECT platform_balance FROM users WHERE id=?', (uid,)).fetchone()
        if user:
            bal = user['platform_balance']
            db.execute('UPDATE users SET platform_balance=0 WHERE id=?', (uid,))
            db.execute('UPDATE finance SET value=value+? WHERE key="balance"',  (bal,))
            db.execute('UPDATE finance SET value=value+? WHERE key="total_in"', (bal,))
            db.execute('INSERT INTO logs (uid,action,type,time) VALUES (?,?,?,?)',
                (uid, f'تصفير رصيد مستخدم ${bal:.2f}', 'finance', now()))
    db.commit()
    db.close()
    return jsonify({'success': True})


# ══════════════════════════════════════════
#  تشغيل
# ══════════════════════════════════════════
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
