# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
import pathlib
import re
import traceback

from crewai.agents.parser import AgentFinish
from crewai.tasks.task_output import TaskOutput
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import urllib.parse

from github_resume_generator.crew import GithubResumeGenerator


STATIC_DIR = pathlib.Path(__file__).parent.parent / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"
KEEPALIVE_INTERVAL_SECS = 5
MAX_KEEPALIVE_SECS = 120

app = FastAPI()
app.mount("/r", StaticFiles(directory=STATIC_DIR), name="static")


async def _process_resume(username: str, output_queue: asyncio.Queue):
    """Starts the resume generation crew, pushing progress to the queue."""
    await output_queue.put({'event': 'progress_update',
                            'status': 'started'})

    resume_loop = asyncio.get_running_loop()

    def update_hook(msg: TaskOutput | AgentFinish) -> None:
        if isinstance(msg, AgentFinish):
            print(json.dumps({
                'thought': msg.thought,
                'output': msg.output,
                'text': msg.text
            }))
            return

        resume_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(output_queue.put({
                'event': 'progress_update',
                'task': msg.name,
                'summary': msg.summary,
                'status': 'task_done'
            }))
        )

    crew = GithubResumeGenerator().crew(task_callback=update_hook, step_callback=update_hook)

    result = await crew.kickoff_async(inputs=dict(username=username))
    await output_queue.put({'status': 'completed', 'output': result.raw})


@app.get("/resume")
async def process_resume_stream(username: str):
    """Handle resume API request, with streamed progress events."""

    username, *_ = re.split(r'\s+', username.strip())
    username = username[:128]

    async def generate_updates():
        update_queue = asyncio.Queue()
        resume_task = asyncio.create_task(_process_resume(username, update_queue))
        data_task = asyncio.create_task(update_queue.get())
        heartbeat_task = asyncio.create_task(asyncio.sleep(KEEPALIVE_INTERVAL_SECS))

        try:
            while True:
                done, pending = await asyncio.wait(
                    [data_task, heartbeat_task],
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=MAX_KEEPALIVE_SECS,
                )

                if data_task in done:
                    update = await data_task
                    print(json.dumps(update))

                    output = ''
                    if event := update.pop('event', None):
                        output += f'event: {event}\n'

                    output += f"data: {json.dumps(update)}\n\n"
                    yield output
                    data_task = asyncio.create_task(update_queue.get())

                    if update.get('status') == 'completed':
                        break

                elif heartbeat_task in done:
                    yield "event: ping\ndata: {}\n\n"
                    heartbeat_task = asyncio.create_task(asyncio.sleep(KEEPALIVE_INTERVAL_SECS))

                elif not done and pending:
                    raise asyncio.TimeoutError("Stream timed out.")

        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'status': 'error', 'message': 'Stream timed out.'})}\n\n"
            print("Stream timed out: No updates received.")

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': f'An error occurred: {str(e)}'})}\n\n"
            print(f"Error during streaming: {e}")
            print(json.dumps({
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }))

        finally:
            if not resume_task.done():
                resume_task.cancel()
            if not heartbeat_task.done():
                heartbeat_task.cancel()
            if not data_task.done():
                data_task.cancel()

            await asyncio.gather(resume_task, heartbeat_task, return_exceptions=True)

    return StreamingResponse(generate_updates(), media_type="text/event-stream")


@app.get("/")
async def home_page(username: str | None = None):
    """Redirect to the index in the static dir."""
    with open(INDEX_HTML_PATH, 'r', encoding='utf-8') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)
