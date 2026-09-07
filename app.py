import os, tempfile, threading
import gradio as gr
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip
from huggingface_hub import InferenceClient
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

HF_TOKEN = os.getenv("HF_TOKEN", "")
TELE_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else None

def make_video_file(prompt, script_text):
    # shared core function for both website and telegram
    short_script = script_text[:120] if script_text else prompt[:120]
    
    tmp_audio = tempfile.mktemp(suffix=".mp3")
    gTTS(text=short_script, lang='en').save(tmp_audio)
    audio = AudioFileClip(tmp_audio)

    img = client.text_to_image(prompt + ", cinematic, 4k", model="black-forest-labs/FLUX.1-schnell")
    tmp_img = tempfile.mktemp(suffix=".jpg")
    img.resize((512, 912)).save(tmp_img)

    clip = ImageClip(tmp_img, duration=audio.duration).set_audio(audio)
    out = tempfile.mktemp(suffix=".mp4")
    clip.write_videofile(out, fps=20, codec='libx264', preset='ultrafast', audio_codec='aac', logger=None)
    return out

# ---------- WEBSITE PART ----------
def generate_web(prompt, script):
    if not client:
        return None, "Add HF_TOKEN in Render"
    try:
        out = make_video_file(prompt, script)
        return out, "DONE ✅"
    except Exception as e:
        return None, f"Error: {str(e)[:800]}"

def launch_gradio():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("# ProtonXona — Script to Video + Audio AI\nWebsite + Telegram Bot (Same App)")
        prompt = gr.Textbox(label="Script / Visual Prompt", value="Ghanaian entrepreneur walking in modern Accra market, confident")
        script = gr.Textbox(label="Voice-over Script (keep 1 sentence for speed)", value="Welcome to ProtonXona, we turn your script into video instantly.")
        btn = gr.Button("Generate Video", variant="primary")
        video = gr.Video(label="Result")
        status = gr.Textbox(label="Status")
        btn.click(generate_web, inputs=[prompt, script], outputs=[video, status])
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)), share=False)

# ---------- TELEGRAM PART ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ProtonXona Bot 🎬\nSend me like this:\nVisual | Voice\nExample:\nGhana lady in market | Welcome to my business\n\nOr just send one line and I use it for both.")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "|" in text:
        prompt, voice = text.split("|", 1)
    else:
        prompt, voice = text, text
    await update.message.reply_text(f"🎬 Generating: {prompt.strip()}\n~30 sec...")
    try:
        out = make_video_file(prompt.strip(), voice.strip())
        await update.message.reply_video(video=open(out, 'rb'), caption="✅ Your ProtonXona Video — Website + Telegram")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)[:800]}")

def launch_telegram():
    if not TELE_TOKEN or not HF_TOKEN:
        print("No TELEGRAM_TOKEN or HF_TOKEN, skipping bot")
        return
    app = Application.builder().token(TELE_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("Telegram Bot Running...")
    app.run_polling()

# ---------- RUN BOTH ----------
if name == "main":
    # Gradio in background thread
    threading.Thread(target=launch_gradio, daemon=True).start()
    # Telegram in main
    launch_telegram()
