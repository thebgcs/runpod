FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime@sha256:c8268a92a69bd500f8be0e665b2630ee006dadaf7bfbc24249141b15ff622755

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from huggingface_hub import hf_hub_download, snapshot_download; snapshot_download(repo_id='CompVis/stable-diffusion-v1-4', revision='133a221b8aa7292a167afc5127cb63fb5005638b', local_dir='/model', allow_patterns=['*.json', '*.txt', '*.fp16.safetensors']); hf_hub_download(repo_id='CompVis/stable-diffusion-license', repo_type='space', filename='license.txt', revision='14d42d09bffd871b1666a084fc954a50cff72ac0', local_dir='/model')"

RUN python -c "from diffusers import AutoPipelineForText2Image"

COPY handler.py .

ENV HF_HUB_OFFLINE=1
ENV PYTHONUNBUFFERED=1

CMD ["python", "handler.py"]
