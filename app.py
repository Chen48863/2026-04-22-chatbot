# === 自動切換工作目錄 ===
import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# === 匯入區塊 ===
from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, desc
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import os
import shutil
import random

# === 資料庫設定 ===
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# === 上傳目錄設定 ===
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === 允許的檔案類型 ===
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# === 資料模型定義 ===

class ChatSession(Base):
    """聊天室模型"""
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, default="新對話")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan",
                            order_by="Message.timestamp")


class Message(Base):
    """訊息模型"""
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" 或 "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    session = relationship("ChatSession", back_populates="messages")
    attachments = relationship("Attachment", back_populates="message", cascade="all, delete-orphan")


class Attachment(Base):
    """附件模型"""
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="attachments")


class Memory(Base):
    """使用者記憶模型"""
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# === 建立資料表 ===
Base.metadata.create_all(bind=engine)

# === Pydantic Schema ===

class SessionCreate(BaseModel):
    title: str = Field(default="新對話", max_length=200)

class SessionUpdate(BaseModel):
    title: str = Field(max_length=200)

class MessageCreate(BaseModel):
    content: str = Field(min_length=1)

class MemoryUpdate(BaseModel):
    key: str = Field(max_length=100)
    value: str

# === FastAPI 應用程式初始化 ===
app = FastAPI(title="智慧聊天機器人", description="支援多輪對話、檔案上傳、記憶機制的聊天機器人", version="1.0.0")

# === 掛載靜態檔案與模板 ===
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# === 資料庫 Session 依賴注入 ===
def get_db():
    """取得資料庫 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Mock AI 回覆模組 ===

MOCK_REPLIES = [
    "您好！這是一個很好的問題。讓我為您詳細說明。",
    "感謝您的提問！根據我的理解，這個問題可以從以下幾個角度來分析...",
    "這是一個有趣的話題！我認為我們可以這樣理解...",
    "好的，讓我幫您整理一下思路。首先，我們需要考慮幾個關鍵因素...",
    "非常感謝您的分享！基於您提供的資訊，我有以下幾點建議...",
    "這個問題值得深入探討。以下是我的分析與看法...",
    "收到！讓我為您提供一些有用的資訊和建議。",
    "好問題！這涉及到幾個重要的概念，讓我一一為您說明。",
    "感謝您的詢問。這個主題相當廣泛，讓我從最核心的部分開始解釋...",
    "了解您的需求了！以下是我的回覆，希望對您有所幫助。",
]

def generate_mock_reply(user_message: str, memory: dict = None) -> str:
    """
    產生 Mock AI 回覆
    預留介面：日後可替換為真實 AI API（如 Google Gemini / OpenAI）
    """
    # 根據使用者訊息內容產生對應的模擬回覆
    if "你好" in user_message or "哈囉" in user_message:
        reply = "您好！😊 很高興為您服務。請問有什麼我可以幫助您的嗎？"
    elif "名字" in user_message or "你是誰" in user_message:
        display_name = memory.get("display_name", "使用者") if memory else "使用者"
        reply = f"我是智慧聊天機器人 🤖，您可以叫我小智。{display_name}，很高興認識您！"
    elif "謝謝" in user_message or "感謝" in user_message:
        reply = "不客氣！😊 如果還有其他問題，隨時都可以問我喔！"
    elif "再見" in user_message or "掰掰" in user_message:
        reply = "再見！👋 祝您有美好的一天！期待下次再和您聊天。"
    else:
        reply = random.choice(MOCK_REPLIES)

    # 加入記憶脈絡
    if memory and memory.get("language") == "英文":
        reply += "\n\n(Note: I notice you prefer English, but I'm currently in mock mode with Chinese responses.)"

    return reply

# === 初始化預設記憶 ===
def init_default_memory(db: Session):
    """初始化預設記憶項目"""
    defaults = {
        "display_name": "使用者",
        "language": "繁體中文",
        "reply_style": "友善"
    }
    for key, value in defaults.items():
        existing = db.query(Memory).filter(Memory.key == key).first()
        if not existing:
            db.add(Memory(key=key, value=value))
    db.commit()

# 啟動時初始化預設記憶
with SessionLocal() as db:
    init_default_memory(db)

# === 取得所有記憶（輔助函式） ===
def get_all_memory(db: Session) -> dict:
    """取得所有記憶並轉為字典"""
    memories = db.query(Memory).all()
    return {m.key: m.value for m in memories}

# === 路由定義 ===

# --- 頁面路由 ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    """首頁 - 聊天介面"""
    sessions = db.query(ChatSession).order_by(desc(ChatSession.updated_at)).all()
    return templates.TemplateResponse(request, "index.html", {
        "sessions": sessions
    })

# --- Session API ---

@app.get("/api/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    """取得所有聊天室列表"""
    sessions = db.query(ChatSession).order_by(desc(ChatSession.updated_at)).all()
    result = []
    for s in sessions:
        last_msg = db.query(Message).filter(
            Message.session_id == s.id
        ).order_by(desc(Message.timestamp)).first()
        result.append({
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
            "message_count": len(s.messages),
            "last_message": last_msg.content[:50] + "..." if last_msg and len(last_msg.content) > 50 else (last_msg.content if last_msg else "")
        })
    return result

@app.post("/api/sessions")
async def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    """建立新聊天室"""
    session = ChatSession(title=data.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: int, db: Session = Depends(get_db)):
    """取得聊天室詳情與所有訊息"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="聊天室不存在")

    messages = []
    for msg in session.messages:
        attachments = [{
            "id": att.id,
            "filename": att.filename,
            "stored_filename": att.stored_filename,
            "file_type": att.file_type,
            "file_size": att.file_size,
            "url": f"/uploads/{att.stored_filename}"
        } for att in msg.attachments]

        messages.append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "attachments": attachments
        })

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "messages": messages
    }

@app.put("/api/sessions/{session_id}")
async def update_session(session_id: int, data: SessionUpdate, db: Session = Depends(get_db)):
    """更新聊天室標題"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="聊天室不存在")
    session.title = data.title
    session.updated_at = datetime.utcnow()
    db.commit()
    return {"id": session.id, "title": session.title}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: int, db: Session = Depends(get_db)):
    """刪除聊天室及其所有訊息與附件"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="聊天室不存在")

    # 刪除相關附件檔案
    for msg in session.messages:
        for att in msg.attachments:
            file_path = os.path.join(UPLOAD_DIR, att.stored_filename)
            if os.path.exists(file_path):
                os.remove(file_path)

    db.delete(session)
    db.commit()
    return {"message": "聊天室已刪除"}

# --- Message API ---

@app.post("/api/sessions/{session_id}/messages")
async def send_message(session_id: int, data: MessageCreate, db: Session = Depends(get_db)):
    """發送訊息並取得 AI 回覆"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="聊天室不存在")

    # 建立使用者訊息
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=data.content,
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)

    # 取得記憶脈絡
    memory = get_all_memory(db)

    # 產生 Mock AI 回覆
    ai_reply_content = generate_mock_reply(data.content, memory)

    # 建立 AI 回覆訊息
    ai_msg = Message(
        session_id=session_id,
        role="assistant",
        content=ai_reply_content,
        timestamp=datetime.utcnow()
    )
    db.add(ai_msg)

    # 更新聊天室的最後更新時間
    session.updated_at = datetime.utcnow()

    # 若是第一則訊息，自動設定聊天室標題
    msg_count = db.query(Message).filter(Message.session_id == session_id).count()
    if msg_count == 0:
        session.title = data.content[:30] + ("..." if len(data.content) > 30 else "")

    db.commit()
    db.refresh(user_msg)
    db.refresh(ai_msg)

    return {
        "user_message": {
            "id": user_msg.id,
            "role": user_msg.role,
            "content": user_msg.content,
            "timestamp": user_msg.timestamp.isoformat(),
            "attachments": []
        },
        "ai_message": {
            "id": ai_msg.id,
            "role": ai_msg.role,
            "content": ai_msg.content,
            "timestamp": ai_msg.timestamp.isoformat(),
            "attachments": []
        }
    }

# --- 重新生成回覆 ---

@app.post("/api/sessions/{session_id}/regenerate")
async def regenerate_reply(session_id: int, db: Session = Depends(get_db)):
    """重新生成最後一則 AI 回覆"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="聊天室不存在")

    # 找到最後一則 AI 訊息
    last_ai_msg = db.query(Message).filter(
        Message.session_id == session_id,
        Message.role == "assistant"
    ).order_by(desc(Message.timestamp)).first()

    if not last_ai_msg:
        raise HTTPException(status_code=404, detail="沒有可重新生成的 AI 回覆")

    # 找到對應的使用者訊息（AI 回覆前一則）
    last_user_msg = db.query(Message).filter(
        Message.session_id == session_id,
        Message.role == "user",
        Message.timestamp <= last_ai_msg.timestamp
    ).order_by(desc(Message.timestamp)).first()

    # 取得記憶脈絡
    memory = get_all_memory(db)

    # 重新生成回覆
    user_content = last_user_msg.content if last_user_msg else ""
    new_reply = generate_mock_reply(user_content, memory)

    # 更新 AI 回覆內容
    last_ai_msg.content = new_reply
    last_ai_msg.timestamp = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(last_ai_msg)

    return {
        "id": last_ai_msg.id,
        "role": last_ai_msg.role,
        "content": last_ai_msg.content,
        "timestamp": last_ai_msg.timestamp.isoformat()
    }

# --- 檔案上傳 API ---

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """上傳檔案至指定聊天室"""
    # 驗證聊天室存在
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="聊天室不存在")

    # 驗證檔案格式
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支援的檔案格式。僅支援：{', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 讀取檔案內容並驗證大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="檔案大小超過 10MB 限制")

    # 使用 UUID 重新命名檔案
    stored_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    # 儲存檔案
    with open(file_path, "wb") as f:
        f.write(content)

    # 建立使用者訊息（附帶檔案說明）
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=f"[已上傳檔案：{file.filename}]",
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)
    db.flush()  # 取得 user_msg.id

    # 建立附件記錄
    attachment = Attachment(
        message_id=user_msg.id,
        filename=file.filename,
        stored_filename=stored_filename,
        file_type=file.content_type or "application/octet-stream",
        file_size=len(content)
    )
    db.add(attachment)

    # 產生 AI 回覆
    memory = get_all_memory(db)
    ai_reply = f"收到您上傳的檔案「{file.filename}」📎。這是一個 {file_ext.upper()} 格式的檔案，大小約 {len(content) / 1024:.1f} KB。請問您需要我如何處理這個檔案呢？"

    ai_msg = Message(
        session_id=session_id,
        role="assistant",
        content=ai_reply,
        timestamp=datetime.utcnow()
    )
    db.add(ai_msg)

    # 更新聊天室時間
    session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user_msg)
    db.refresh(attachment)
    db.refresh(ai_msg)

    return {
        "user_message": {
            "id": user_msg.id,
            "role": user_msg.role,
            "content": user_msg.content,
            "timestamp": user_msg.timestamp.isoformat(),
            "attachments": [{
                "id": attachment.id,
                "filename": attachment.filename,
                "stored_filename": attachment.stored_filename,
                "file_type": attachment.file_type,
                "file_size": attachment.file_size,
                "url": f"/uploads/{attachment.stored_filename}"
            }]
        },
        "ai_message": {
            "id": ai_msg.id,
            "role": ai_msg.role,
            "content": ai_msg.content,
            "timestamp": ai_msg.timestamp.isoformat(),
            "attachments": []
        }
    }

# --- Memory API ---

@app.get("/api/memory")
async def get_memory(db: Session = Depends(get_db)):
    """取得所有使用者記憶"""
    memories = db.query(Memory).all()
    return [{
        "id": m.id,
        "key": m.key,
        "value": m.value,
        "updated_at": m.updated_at.isoformat()
    } for m in memories]

@app.put("/api/memory")
async def update_memory(data: MemoryUpdate, db: Session = Depends(get_db)):
    """更新使用者記憶"""
    memory = db.query(Memory).filter(Memory.key == data.key).first()
    if memory:
        memory.value = data.value
        memory.updated_at = datetime.utcnow()
    else:
        memory = Memory(key=data.key, value=data.value)
        db.add(memory)
    db.commit()
    db.refresh(memory)
    return {
        "id": memory.id,
        "key": memory.key,
        "value": memory.value,
        "updated_at": memory.updated_at.isoformat()
    }

# === 啟動伺服器 ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
