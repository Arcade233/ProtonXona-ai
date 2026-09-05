import gradio as gr
import torch
from diffusers import StableDiffusionPipeline
import os

# FAST model for FREE Render - still 720x1280 clear
model_id = "runwayml/stable-diffusion-v1-5"
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
pipe = pipe.to("cpu")
pipe.enable_attention_slicing()

def generate(prompt):
    image = pipe(prompt, height=1280, width=720, num_inference_steps=20).images[0]
    image.save("output.png")
    return image, f"Done! Prompt: {prompt}"

with gr.Blocks() as demo:
    gr.Markdown("# ProtonXona Video Generator - FREE on Render")
    inp = gr.Textbox(label="Enter prompt", placeholder="beautiful african queen, ultra clear 8k")
    btn = gr.Button("Generate Image")
    out_img = gr.Image(label="Result 720x1280")
    out_txt = gr.Textbox(label="Status")
    btn.click(generate, inputs=inp, outputs=[out_img, out_txt])

# Render needs this port
demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 10000)))
