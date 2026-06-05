# 🧠 QuizMasterUz Bot

Telegram quiz boti — .docx fayl asosida savollar beradi.

---

## 📁 Loyiha tuzilmasi

```
quizbot/
├── main.py                  # Asosiy fayl
├── requirements.txt         # Kutubxonalar
├── railway.toml             # Railway config
├── .env.example             # Environment o'zgaruvchilar namunasi
├── database/
│   └── db.py               # PostgreSQL funksiyalar
├── handlers/
│   ├── user.py             # Foydalanuvchi handlerlari
│   └── admin.py            # Admin panel handlerlari
├── utils/
│   ├── parser.py           # .docx parser
│   └── keyboards.py        # Telegram tugmalar
└── locales/
    └── texts.py            # O'zbek/Rus/Ingliz matnlar
```

---

## ⚙️ O'rnatish (Railway)

### 1. .env sozlash
```
BOT_TOKEN=<BotFather tokeningiz>
ADMIN_ID=<Sizning Telegram ID>
DATABASE_URL=postgresql://...
```

### 2. Railway'da deploy
1. [railway.app](https://railway.app) ga kiring
2. **New Project → Deploy from GitHub repo**
3. PostgreSQL qo'shing: **Add Service → Database → PostgreSQL**
4. `DATABASE_URL` o'zgaruvchisini nusxalab bot servisiga qo'shing
5. `BOT_TOKEN` va `ADMIN_ID` ni ham qo'shing
6. Deploy!

---

## 📄 .docx fayl formati

```
# QUIZ: Quiz nomi

Q1: Savol matni?
A) Birinchi variant
B) Ikkinchi variant
C) Uchinchi variant
D) To'rtinchi variant
ANSWER: B

Q2: Ikkinchi savol?
A) Variant A
B) Variant B
C) Variant C
D) Variant D
ANSWER: A
```

**Qoidalar:**
- `# QUIZ:` — quiz nomi (bir marta)
- `Q1, Q2, Q3...` — savollar ketma-ketligi
- Faqat `A) B) C) D)` variantlar
- `ANSWER:` — faqat bitta harf
- Har bir savoldan keyin bo'sh qator

---

## 👑 Admin imkoniyatlari

### Super Admin (siz):
- ✅ Barcha foydalanuvchilar ro'yxati
- ✅ Obunalilar ro'yxati
- ✅ Obunaga qo'shish / olish
- ✅ Narx belgilash
- ✅ Admin qo'shish / o'chirish
- ✅ Barcha admin loglari
- ✅ Broadcast xabar yuborish
- ✅ Foydalanuvchi qidirish

### Oddiy Admin:
- ✅ Foydalanuvchilar ko'rish
- ✅ Obunaga qo'shish / olish
- ✅ O'z loglari
- ❌ Narx o'zgartira olmaydi
- ❌ Admin qo'sha olmaydi
- ❌ Broadcast qila olmaydi

---

## 🌐 Tillar
- 🇺🇿 O'zbek
- 🇷🇺 Русский
- 🇬🇧 English

---

## 📊 Bot imkoniyatlari
- Bir vaqtda **cheksiz** foydalanuvchilarga xizmat qiladi
- Har bir foydalanuvchining statistikasi saqlanadi
- Barcha admin harakatlari loglanadi
- PostgreSQL — katta ma'lumotlar bazasi

---

## 🆔 Muhim ma'lumotlar
- **Bot token:** BotFather'dan oling
- **Admin ID:** @userinfobot orqali bilib oling
- **Database:** Railway PostgreSQL (bepul)
