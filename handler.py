import base64
import io
import secrets


MODEL_ID = "CompVis/stable-diffusion-v1-4"


def generate_image(job, pipeline, torch):
    data = job.get("input") if isinstance(job, dict) else None
    if not isinstance(data, dict):
        return {"error": "input must be an object."}

    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return {"error": "prompt must be a non-empty string."}

    seed = data.get("seed")
    if seed is None:
        seed = secrets.randbits(32)
    if type(seed) is not int or not 0 <= seed <= 4294967295:
        return {"error": "seed must be an integer between 0 and 4294967295."}

    generator = torch.Generator(device="cuda").manual_seed(seed)
    with torch.inference_mode():
        result = pipeline(
            prompt=prompt.strip(),
            generator=generator,
            height=512,
            width=512,
            num_inference_steps=25,
            guidance_scale=7.5,
        )

    image = io.BytesIO()
    result.images[0].save(image, format="PNG")
    flagged = result.nsfw_content_detected

    return {
        "image_base64": base64.b64encode(image.getvalue()).decode("ascii"),
        "content_type": "image/png",
        "seed": seed,
        "model": MODEL_ID,
        "nsfw_content_detected": bool(flagged[0]) if flagged is not None else None,
    }


def main():
    import runpod
    import torch
    from diffusers import AutoPipelineForText2Image

    pipeline = AutoPipelineForText2Image.from_pretrained(
        "/model",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
        local_files_only=True,
    ).to("cuda")

    def handler(job):
        return generate_image(job, pipeline, torch)

    runpod.serverless.start({"handler": handler})


if __name__ == "__main__":
    main()
