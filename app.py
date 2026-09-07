import os
import tempfile
import threading
import time
import gradio as gr
from gtts import gTTS
from huggingface_hub import InferenceClient
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Robust MoviePy import compatibility
try:
    from moviepy.editor import ImageClip, AudioFileClip
except ModuleNotFoundError:
    from moviepy import ImageClip, AudioFileClip

# ---------------- ENVIRONMENT & TOKENS ----------------
HF_TOKEN = os.getenv("HF_TOKEN", "")
TELE_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Standard InferenceClient initialization
client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else None

# ---------------- CORE VIDEO GENERATION ----------------
def make_video_file(prompt: str, script_text: str) -> str:
    """Shared core function for generating video from prompt and voice script."""
    if not client:
        raise ValueError("HF_TOKEN is missing. Please set it in your environment variables.")

    short_script = script_text[:120] if script_text else prompt[:120]

    # 1. Generate Voiceover Audio (gTTS)
    tmp_audio = tempfile.mktemp(suffix=".mp3")
    tts = gTTS(text=short_script, lang="en")
    tts.save(tmp_audio)
    audio = AudioFileClip(tmp_audio)

    # 2. Generate Image via Hugging Face Inference API with Retry Logic
    full_prompt = f"{prompt}, cinematic, 4k high quality"
    img = None
    
    for attempt in range(3):
        try:
            img = client.text_to_image(full_prompt, model="black-forest-labs/FLUX.1-schnell")
            break
        except Exception as err:
            if attempt == 2:
                raise err
            time.sleep(2)  # Wait 2 seconds before retrying
    
    # Resize Image (PIL format)
    img = img.resize((512, 912))
    tmp_img = tempfile.mktemp(suffix=".jpg")
    img.save(tmp_img)

    # 3. Create Video Clip from Image + Audio
    clip = ImageClip(tmp_img)
    
    if hasattr(clip, "with_duration"):
        clip = clip.with_duration(audio.duration)
    else:
        clip = clip.set_duration(audio.duration)

    if hasattr(clip, "with_audio"):
        clip = clip.with_audio(audio)
    else:
        clip = clip.set_audio(audio)

    out_video = tempfile.mktemp(suffix=".mp4")
    clip.write_videofile(
        out_video,
        fps=20,
        codec="libx264",
        preset="ultrafast",
        audio_codec="aac",
        logger=None,
    )
    
    clip.close()
    audio.close()

    return out_video

# ---------------- GRADIO WEBSITE INTERFACE ----------------
def generate_web(prompt: str, script: str):
    if not HF_TOKEN:
        return None, "Error: HF_TOKEN environment variable is missing!"
    try:
        out = make_video_file(prompt, script)
        return out, "DONE ✅"
    except Exception as e:
        return None, f"Error: {str(e)[:800]}"

def launch_gradio():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("# ProtonXona — Script to Video AI Generator\n### Website + Telegram Bot")
        
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(
                    label="Visual Prompt",
                    value="Ghanaian entrepreneur walking in modern Accra market, confident",
                )
                script = gr.Textbox(
                    label="Voice-over Script (Keep short for speed)",
                    value="Welcome to ProtonXona, we turn your script into video instantly.",
                )
                btn = gr.Button("🎬 Generate Video", variant="primary")
            
            with gr.Column():
                video = gr.Video(label="Generated Result")
                status = gr.Textbox(label="Status")

        btn.click(generate_web, inputs=[prompt, script], outputs=[video, status])

    port = int(os.environ.get("PORT", 10000))
    demo.launch(server_name="0.0.0.0", server_port=port, share=False)

# ---------------- TELEGRAM BOT INTERFACE ----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 **ProtonXona AI Video Generator Bot**\n\n"
        "Send your request using this format:\n"
        "`Visual Prompt | Voiceover Text`\n\n"
        "**Example:**\n"
        "`Ghana lady in market | Welcome to my business`\n\n"
        "Or just send a single line of text to use it for both!",
        parse_mode="Markdown",
    )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    
    if "|" in text:
        prompt, voice = text.split("|", 1)
    else:
        prompt, voice = text, text

    prompt = prompt.strip()
    voice = voice.strip()

    status_msg = await update.message.reply_text(
        f"🎬 Generating video for:\n`{prompt}`\n\nPlease wait ~30 seconds...", 
        parse_mode="Markdown"
    )

    try:
        out_path = make_video_file(prompt, voice)
        with open(out_path, "rb") as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ **Your ProtonXona AI Video is Ready!**",
                parse_mode="Markdown",
            )
        await status_msg.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Error generating video: {str(e)[:800]}")

def launch_telegram():
    if not TELE_TOKEN:
        print("⚠️ TELEGRAM_TOKEN missing. Skipping Telegram bot initialization...")
        return
    
    app = Application.builder().token(TELE_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    print("🚀 Telegram Bot listening for messages...")
    app.run_polling(drop_pending_updates=True)

# ---------------- MAIN EXECUTION ----------------
if __name__ == "__main__":
    gradio_thread = threading.Thread(target=launch_gradio, daemon=True)
    gradio_thread.start()
    launch_telegram()
