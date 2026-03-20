# WittenWeb — Flask + SQLite

## الملفات
```
app.py                    ← الخادم الرئيسي (Python)
requirements.txt          ← المكتبات
Procfile                  ← للرفع على Render
wittenweb.db              ← قاعدة البيانات (تُنشأ تلقائياً)
templates/
  index.html              ← المتجر الرئيسي  →  /
  admin.html              ← لوحة المالك     →  /admin
  finance.html            ← حساب الدفع      →  /finance
```

## تشغيل محلياً
```bash
pip install -r requirements.txt
python app.py
```
افتح: http://localhost:5000

## الرفع على Render (مجاني)
1. ارفع المجلد على GitHub
2. render.com → New → Web Service
3. اختر المستودع
4. Build: `pip install -r requirements.txt`
5. Start: `gunicorn app:app`
6. Deploy ✅

## كلمات المرور
| الصفحة | كلمة المرور |
|--------|-------------|
| /admin | Ww@Admin#9X2mK!47 |
| /finance | Ww$Finance!8Tz3#Qp |

## API
| Method | Endpoint | الوظيفة |
|--------|----------|---------|
| POST | /api/register | تسجيل مستخدم |
| POST | /api/login | تسجيل دخول |
| GET | /api/users | جميع المستخدمين |
| DELETE | /api/users/<id> | حذف مستخدم |
| POST | /api/users/<id>/zero | تصفير رصيد |
| POST | /api/users/<id>/rating | تقييم التاجر |
| POST | /api/users/<id>/imposter | علامة انتحال |
| GET | /api/products | المنتجات |
| POST | /api/products | إضافة منتج |
| DELETE | /api/products/<id> | حذف منتج |
| POST | /api/checkout | إتمام شراء |
| GET | /api/notes | الملاحظات |
| POST | /api/notes | إضافة ملاحظة |
| GET | /api/logs | السجل |
| DELETE | /api/logs | مسح السجل |
| GET | /api/finance | رصيد الدفع |
| POST | /api/finance/transfer | تحويل رصيد |
| POST | /api/finance/add | إضافة رصيد |
| POST | /api/finance/zero | تصفير |
