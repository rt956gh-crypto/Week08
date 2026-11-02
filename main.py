import os
import random
import uuid
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Wordle API Server")

# 目前 client 是桌面程式，不受瀏覽器 CORS 限制。若日後改成網頁，
# 再把 allow_origins 限定為實際前端網址。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 簡易單字庫
WORD_BANK = ["APPLE", "TRAIN", "HOUSE", "PLANT", "SMART", "WORLD", "LIGHT", "BRAIN", "CLOUD", "WATER"]

# 記憶體儲存遊戲狀態：{game_id: {"target": "APPLE", "status": "PLAYING"}}
games_db: Dict[str, dict] = {}


class GuessRequest(BaseModel):
    game_id: str
    guess: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/new-game")
def start_new_game():
    """ 建立新一局遊戲，回傳 game_id """
    game_id = str(uuid.uuid4())
    target_word = random.choice(WORD_BANK)
    games_db[game_id] = {
        "target": target_word,
        "status": "PLAYING"
    }
    return {"game_id": game_id, "message": "New game started!"}


@app.post("/api/guess")
def process_guess(req: GuessRequest):
    if req.game_id not in games_db:
        raise HTTPException(status_code=404, detail="Game session not found.")
    guess = req.guess.upper()
    if len(guess) != 5 or not guess.isascii() or not guess.isalpha():
        raise HTTPException(status_code=400, detail="Guess must be 5 English letters.")
    target = games_db[req.game_id]["target"]
    feedback = ["absent"] * 5
    counts = {}
    for letter in target:
        counts[letter] = counts.get(letter, 0) + 1
    for i in range(5):
        if guess[i] == target[i]:
            feedback[i] = "correct"
            counts[guess[i]] -= 1
    for i in range(5):
        if feedback[i] != "correct" and counts.get(guess[i], 0) > 0:
            feedback[i] = "present"
            counts[guess[i]] -= 1
    is_correct = (guess == target)
    if is_correct:
        games_db[req.game_id]["status"] = "WON"
    return {
    "guess": guess,
    "feedback": feedback,
    "is_correct": is_correct,
    "target_word": target if is_correct else None
    }

if __name__ == "__main__":
    import uvicorn
    # Render 會透過 PORT 環境變數指定服務埠；本機則預設使用 8000。
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

