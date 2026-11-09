# Runpod image generation

A queue-based Runpod Serverless worker that generates a 512 x 512 PNG from a text prompt. The worker loads Stable Diffusion v1.4 once when it starts and returns the image as base64.

## Requirements

- A Runpod account with credits and an API key.
- Docker with Buildx and an account with a container registry that Runpod can access.
- A GPU with sufficient memory. Start with a 16 GB GPU and check availability and pricing in Runpod.
- [Bruno](https://www.usebruno.com/) to send the requests.
- Python 3 to save the image and run the local tests.

The model uses the [CreativeML Open RAIL-M license](https://huggingface.co/spaces/CompVis/stable-diffusion-license). Review its terms before distributing the image. The model license is included in the container at `/model/license.txt`.

## Build and deploy

Replace `REGISTRY/IMAGE` with your container image name.

```sh
docker buildx build --platform linux/amd64 --tag REGISTRY/IMAGE:1.0.0 --load .
docker push REGISTRY/IMAGE:1.0.0
```

The build downloads the model into the image. The model revision and base image are pinned in the Dockerfile. No model download is needed when the worker starts.

In Runpod, create a Serverless endpoint using the container image:

1. Choose a queue-based endpoint and enter `REGISTRY/IMAGE:1.0.0`.
2. Select a GPU and one GPU per worker.
3. Set active workers to `0` and max workers to `1`.
4. Deploy the endpoint and copy its endpoint ID.

Runpod charges for a worker while it starts, processes jobs, and waits during its idle timeout. Check your balance and the endpoint settings before running requests. See [Runpod Serverless pricing](https://docs.runpod.io/serverless/pricing) and [endpoint settings](https://docs.runpod.io/serverless/endpoints/endpoint-configurations).

## Send a request with Bruno

1. Open the `bruno` folder as a collection in Bruno.
2. Select the `Runpod` environment and set `endpoint_id` to your endpoint ID.
3. Set `runpod_api_key` as a secret in the environment. Bruno stores the secret value locally, outside the collection file.
4. Run **Generate image**. The response contains a job ID, which the collection stores for the next request.
5. Run **Check status** until the job is `COMPLETED` or a failure status appears. The first request can take longer while the worker starts.
6. Save the completed response body as `response.json`, then run:

```sh
python3 scripts/save_image.py response.json image.png
```

The **Empty prompt** request submits an invalid job. Run **Check status** after it and inspect the error. The Runpod SDK handles a returned `error` as a job error; model and runtime exceptions are also reported as errors.

Runpod retains results from asynchronous requests for 30 minutes after completion. Save the response before it expires. See [Send API requests](https://docs.runpod.io/serverless/endpoints/send-requests).

## Request and response

The request body uses the Runpod `input` object:

```json
{
  "input": {
    "prompt": "A small lighthouse on a rocky coast at sunset, watercolor painting",
    "seed": 42
  }
}
```

`prompt` is required. `seed` is optional and must be an integer from `0` to `4294967295`. If omitted, the worker generates one and returns it with the result.

A completed job includes these fields under `output`:

```json
{
  "image_base64": "<base64-encoded PNG>",
  "content_type": "image/png",
  "seed": 42,
  "model": "CompVis/stable-diffusion-v1-4",
  "nsfw_content_detected": false
}
```

The safety checker result can be `true`, `false`, or `null`. The seed helps repeat a request, but the output can vary across hardware and library versions.

## Local tests

```sh
python3 -m unittest discover -s tests -v
```

These tests use a simulated model to check input validation, response encoding, and the image-saving script. They do not test GPU inference or a deployed endpoint.

The container also completed an offline CPU inference at 64 x 64 with one step. The full-size request has not yet been tested on Runpod.

## Troubleshooting

- **The job stays in the queue:** check worker availability, endpoint limits, and the worker logs in Runpod.
- **The worker fails during startup:** check the image pull, model loading, GPU compatibility, and logs.
- **The job returns an error:** check the prompt, seed, and worker logs. A successful HTTP response can still contain a job error.
- **The saved image is missing:** copy the full completed response body from Bruno and run the save command before the result expires.

Model: [CompVis/stable-diffusion-v1-4](https://huggingface.co/CompVis/stable-diffusion-v1-4). Runpod worker reference: [Handler functions](https://docs.runpod.io/serverless/workers/handler-functions).
