import gradio as gr, os, requests
from PIL import Image
import io

HF_TOKEN = os.environ.get("HF_TOKEN", "")
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

def generate(prompt):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt}
    response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    
    if response.status_code != 200:
        return None, f"Error: {response.text}. Wait 20s and retry, model is loading."
    
    image = Image.open(io.BytesIO(response.content))
    image = image.resize((720, 1280))
    image.save("output.png")
    return image, f"Done! {prompt}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona Generator - FREE No RAM")
    inp = gr.Textbox(label="Prompt")
    btn = gr.Button("Generate 720x1280")
    out_img = gr.Image(label="Result")
    out_txt = gr.Textbox(label="Status")
    btn.click(generate, inputs=inp, outputs=[out_img, out_txt])

demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
