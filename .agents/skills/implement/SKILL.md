---
name: Implement
description: 當使用者要求生成程式碼實作時，AI Agent 應依照以下結構產出完整的可執行專案程式碼，使用 FastAPI + SQLite 後端與 HTML 前端。
---
# Implement（程式碼實作）Skill

## 描述

此技能用於生成完整的可執行專案程式碼。當使用者要求實作功能或建立專案時，AI Agent 應依照以下規範產出所有必要的程式碼檔案，確保專案可直接執行。

## 技術棧（Technology Stack）

| 層級 | 技術 | 說明 |
|------|------|------|
| **前端** | HTML + CSS + JavaScript | 使用 Jinja2 模板引擎，放置於 `templates/` 資料夾 |
| **後端** | FastAPI | Python 非同步 Web 框架，負責 API 路由與業務邏輯 |
| **資料庫** | SQLite | 輕量級嵌入式關聯資料庫，使用 SQLAlchemy ORM 操作 |
| **ORM** | SQLAlchemy | 資料庫模型定義與查詢 |
| **模板引擎** | Jinja2 | FastAPI 整合 Jinja2 渲染 HTML 頁面 |

## 觸發條件

當使用者提出以下類型的請求時啟用此技能：
- 「/implement」
- 「幫我實作程式碼」
- 「生成專案程式碼」
- 「建立應用程式」
- 「幫我寫程式」
- 「產生可執行的程式碼」

## 產出檔案結構

執行此技能時，**必須**產出以下檔案與資料夾：

```
project/
├── app.py                  # FastAPI 主程式（進入點）
├── requirements.txt        # Python 套件依賴清單
├── templates/              # HTML 前端模板資料夾
│   ├── base.html           # 基礎模板（共用 Layout）
│   ├── index.html          # 首頁模板
│   └── [其他頁面].html      # 依需求新增的頁面模板
├── static/                 # 靜態資源資料夾（如有需要）
│   ├── css/
│   │   └── style.css       # 自訂樣式
│   └── js/
│       └── main.js         # 自訂 JavaScript
└── database.db             # SQLite 資料庫檔案（執行時自動產生）
```

## 各檔案規範

### 1. `app.py`（主程式）

此檔案為專案的唯一進入點，必須包含以下內容：

```python
# === 匯入區塊 ===
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

# === 資料庫設定 ===
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# === 資料模型定義 ===
# 依照 Models Skill 產出的資料模型定義在此
class ExampleModel(Base):
    __tablename__ = "examples"
    id = Column(Integer, primary_key=True, index=True)
    # ... 其他欄位

# === 建立資料表 ===
Base.metadata.create_all(bind=engine)

# === FastAPI 應用程式初始化 ===
app = FastAPI(title="專案名稱", description="專案描述", version="1.0.0")

# === 掛載靜態檔案與模板 ===
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# === 資料庫 Session 依賴注入 ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === 路由定義 ===

# 首頁
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("index.html", {"request": request})

# CRUD API 路由
# POST - 新增
# GET - 查詢
# PUT - 更新
# DELETE - 刪除

# === 啟動伺服器 ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
```

#### `app.py` 必備元素清單：
- [ ] FastAPI 應用程式實例化
- [ ] SQLAlchemy 資料庫連線設定（SQLite）
- [ ] 資料模型（Model）定義
- [ ] 自動建立資料表（`Base.metadata.create_all`）
- [ ] Jinja2 模板引擎設定
- [ ] 靜態檔案掛載（如有 `static/` 資料夾）
- [ ] 資料庫 Session 依賴注入函式（`get_db`）
- [ ] 頁面渲染路由（回傳 HTML）
- [ ] CRUD API 路由（依需求）
- [ ] Uvicorn 啟動設定

---

### 2. `templates/`（HTML 前端模板）

#### 2.1 `templates/base.html`（基礎模板）

所有頁面必須繼承此基礎模板，確保一致的頁面結構：

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}專案名稱{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', path='css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- 導航列 -->
    <nav>
        <a href="/">首頁</a>
        <!-- 其他導航連結 -->
    </nav>

    <!-- 主要內容 -->
    <main>
        {% block content %}{% endblock %}
    </main>

    <!-- 頁尾 -->
    <footer>
        <p>&copy; {{ year }} 專案名稱</p>
    </footer>

    <script src="{{ url_for('static', path='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### 2.2 `templates/index.html`（首頁模板）

```html
{% extends "base.html" %}

{% block title %}首頁 - 專案名稱{% endblock %}

{% block content %}
<h1>歡迎使用專案名稱</h1>
<!-- 頁面主要內容 -->
{% endblock %}
```

#### 2.3 其他頁面模板

依照功能需求新增對應的 HTML 模板，例如：
- `create.html` — 新增資料表單頁面
- `detail.html` — 資料詳情頁面
- `edit.html` — 編輯資料表單頁面
- `list.html` — 資料列表頁面

#### HTML 模板規範：
- [ ] 所有頁面必須繼承 `base.html`
- [ ] 使用 Jinja2 語法（`{{ }}`、`{% %}`）處理動態資料
- [ ] 表單提交使用 `<form>` 標籤搭配適當的 `action` 與 `method`
- [ ] 頁面語言設定為 `zh-Hant`（繁體中文）
- [ ] 包含 `<meta viewport>` 確保響應式設計
- [ ] 前端樣式應美觀大方，使用現代 CSS 設計

---

### 3. `requirements.txt`（套件依賴清單）

必須包含以下基礎套件：

```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
sqlalchemy>=2.0.0
jinja2>=3.1.0
python-multipart>=0.0.6
aiofiles>=23.0.0
```

#### 規範：
- [ ] 所有套件必須指定**最低版本號**
- [ ] 僅列出專案**直接依賴**的套件
- [ ] 不包含開發用套件（如 pytest），除非使用者要求
- [ ] 確保版本號與程式碼中使用的功能相容

---

## 程式碼品質規範

### 命名慣例
| 項目 | 慣例 | 範例 |
|------|------|------|
| 檔案名稱 | snake_case | `app.py`、`user_model.py` |
| 類別名稱 | PascalCase | `UserModel`、`ItemSchema` |
| 函式名稱 | snake_case | `get_user`、`create_item` |
| 變數名稱 | snake_case | `user_name`、`item_list` |
| 常數 | UPPER_SNAKE_CASE | `DATABASE_URL`、`MAX_ITEMS` |
| 路由路徑 | kebab-case | `/api/user-list`、`/create-item` |

### 必備實作項目
- [ ] **錯誤處理**：所有路由必須包含適當的錯誤處理（try-except / HTTPException）
- [ ] **輸入驗證**：使用 Pydantic 或 Form 驗證使用者輸入
- [ ] **CORS 設定**：如有前後端分離需求，需設定 CORS middleware
- [ ] **註解**：關鍵函式與複雜邏輯需加上中文註解
- [ ] **型別提示**：函式參數與回傳值需加上 Type Hints

### 安全性要求
- [ ] 密碼欄位必須使用雜湊處理（如 bcrypt），不可明文儲存
- [ ] SQL 查詢必須使用 ORM 參數化查詢，防止 SQL Injection
- [ ] 使用者輸入必須進行驗證與清理
- [ ] 敏感設定（如 SECRET_KEY）應使用環境變數

## 執行方式

產出的程式碼應可透過以下步驟執行：

```bash
# 1. 安裝依賴套件
pip install -r requirements.txt

# 2. 啟動應用程式
python app.py

# 3. 開啟瀏覽器訪問
# http://127.0.0.1:8000
```

## 注意事項

- 所有程式碼中的**註解與使用者介面文字**應以**繁體中文**撰寫
- 產出的程式碼必須**可直接執行**，不需額外修改
- 資料庫檔案（`database.db`）應在程式首次執行時自動建立
- 模板渲染必須使用 **Jinja2**，不可使用其他模板引擎
- 所有 CRUD 操作必須有對應的**頁面**或 **API 端點**
- 前端頁面應具備**基本美觀性**，至少包含排版與間距設計
- 若 PRD 或 Architecture 文件已存在，應參考其內容進行實作
- 若 Models 文件已存在，應嚴格依照其定義建立資料模型
