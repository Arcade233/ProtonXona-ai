import gradio as gr
import os
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN", "")
client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else InferenceClient()

def generate(prompt):
    try:
        if not prompt or len(prompt) < 3:
            return None, "Please type a longer prompt"
        # FLUX Schnell = fastest, works free
        image = client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )
        return image, f"Success! Prompt: {prompt}"
    except Exception as e:
        return None, f"ERROR DETAILS: {str(e)[:800]}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona Generator - FIXED")
    inp = gr.Textbox(label="Prompt", value="Beautiful Ghanaian woman in studio, 8k")
    btn = gr.Button("Generate 720x1280")
    out_img = gr.Image(label="Result")
    out_txt = gr.Textbox(label="Status - read error here")
    btn.click(generate, inputs=inp, outputs=[out_img, out_txt])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
