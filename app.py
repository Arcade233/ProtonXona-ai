import gradio as gr, asyncio, torch
import edge_tts
from diffusers import StableDiffusionPipeline
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# SDXL = VERY CLEAR
pipe = StableDiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16, variant="fp16"
)
pipe.to("cuda" if torch.cuda.is_available() else "cpu")

async def make_voice(text, path):
    await edge_tts.Communicate(text, "en-US-AriaNeural", rate="+5%").save(path)

def script_to_video(script):
    scenes = [s.strip() for s in script.split('.') if s.strip()][:6]
    clips = []

    for i, line in enumerate(scenes):
        if len(line) < 5: continue

        # 1. VERY CLEAR IMAGE - 720x1280
        image = pipe(
            prompt=f"{line}, ultra clear, 8k, highly detailed, sharp focus, cinematic lighting, professional",
            negative_prompt="blurry, low quality, low res, bad anatomy, watermark, text",
            height=1280,
            width=720,
            num_inference_steps=30,
            guidance_scale=9
        ).images[0]

        # Upscale to crystal clear
        image = image.resize((1080, 1920), Image.LANCZOS)
        img_path = f"/tmp/img_{i}.png"
        image.save(img_path, quality=95)

        # 2. CLEAR AUDIO
        audio_path = f"/tmp/audio_{i}.mp3"
        asyncio.run(make_voice(line, audio_path))
        audio = AudioFileClip(audio_path)

        # 3. VIDEO + SUBTITLE + ZOOM
        img_clip = (ImageClip(img_path)
                  .set_duration(audio.duration)
                  .fx(vfx.resize, lambda t: 1 + 0.02*t)) # slow zoom for clarity

        # Subtitle
        txt = TextClip(line[:80], fontsize=45, color='white', stroke_color='black', stroke_width=2, font='Arial-Bold', method='caption', size=(900, None))
        txt = txt.set_position(('center', 0.80), relative=True).set_duration(audio.duration)

        video = CompositeVideoClip([img_clip, txt]).set_audio(audio)
        clips.append(video)

    # 4. STITCH TO 3 MIN
    final = concatenate_videoclips(clips)
    out = "/tmp/protonxona_CLEAR_3min.mp4"
    final.write_videofile(out, fps=24, codec="libx264", audio_codec="aac", bitrate="8000k", preset="ultrafast")
    return out

gr.Interface(
    fn=script_to_video,
    inputs=gr.Textbox(lines=6, placeholder="Enter script. Each sentence = 1 scene. Eg: A boy in Accra finds magic phone. He checks football odds. He wins big."),
    outputs=gr.Video(label="Your CLEAR 3-Min Video"),
    title="ProtonXona AI - CLEAR 3-Min Generator (Script + Voice + Subs)"
).launch(server_name="0.0.0.0", server_port=10000)
