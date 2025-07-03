# GitHub Resume Generator - Gemini API x CrewAI

Use the [Gemini API](https://ai.google.dev/gemini-api/) and [CrewAI](https://crewai.com)
to generate a CV/Resume from a GitHub profile, using CrewAI to manage
a crew of agents, and using the Gemini API with Google Search Grounding to
research and write the content.

## Demo

![Demo of GitHub Resume Generator](assets/demo.gif)

*The app in action: Enter a GitHub username and watch as AI agents research and generate a professional resume*

## How it works

A crew is defined that follows a short plan:

* Research the user's GitHub profile
* Research any projects from the profile
* Generate a CV/Resume in Markdown format

You can see the CrewAI configuration in [the config
dir](src/github_resume_generator/config/). Also check out the [custom LLM
class](src/github_resume_generator/crew.py) that uses the `google_search` tool
with CrewAI.

The agents all use the Gemini API, by default [Gemini 2.5
Flash](https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash-preview).
The agent defined for the research task uses the Gemini API's [Google Search
Grounding](https://ai.google.dev/gemini-api/docs/grounding) feature to look up
any relevant information on the supplied user's GitHub profile. This is easy to
implement, runs pretty quickly and can grab any relevant GitHub information from
around the web.

The Crew is wrapped in a FastAPI that serves a streaming endpoint. This API
streams progress updates to indicate as tasks complete, and eventually returns a
message with the resume, in markdown.

The web frontend is just a static HTML page that calls the API and renders
updates. If you want to develop something more complex, the API is serving the
HTML as a static route, so you can deploy a separate web app pointed at the API.

## Installation

This project uses [UV](https://docs.astral.sh/uv/) for Python dependency management and package handling.

### Initial setup

First, if you haven't already, install `uv`:

```bash
pipx install uv
```

> [!NOTE]
> Check out the extensive list of [`uv` installation options](https://docs.astral.sh/uv/getting-started/installation/#installation-methods), including instructions for macOS, Windows, Docker and more.

Next, navigate to your project directory and install the dependencies:

```bash
uv sync
```

#### API key

Grab an API key from [Google AI Studio](https://aistudio.google.com/apikey) and
add it to the `.env` file as `GEMINI_API_KEY`.

```bash
cp .env.example .env
# Now edit .env and add add your key to the GEMINI_API_KEY line.
```

You can now choose to run the API service locally or with Docker. Read one of
the the next two sections depending on what you prefer. Docker will need to be
installed, or just run locally using the already-installed tools.

### Run locally

Run the service. Use `--reload` to automatically refresh while you're editing.

```bash
uv run uvicorn api.service:app --reload
```

With the API server running, browse to http://localhost:8000/

### Docker

To build and run a docker image locally, using a specified API key:

```bash
docker build -t resume-generator-backend-local:latest .
docker run -p 8000:8080 -e GEMINI_API_KEY=your_api_key_here --name my-resume-generator-app-local resume-generator-backend-local:latest
```

With the API server running, browse to the docker port, http://localhost:8080/

The Docker container can also be deployed directly to [Google Cloud Run](https://cloud.google.com/run).

## Running the Crew

To run your crew of AI agents directly, without an API server, run this from the root folder of your project. Pass your GitHub username as the last argument to generate their resume.

```bash
uv run github_resume_generator yourgithubusername
```

You will get a markdown file created in the same directory, `yourgithubusername_resume.md`. Load it in your favourite markdown renderer, e.g. [`glow`](https://github.com/charmbracelet/glow).


## Disclaimer

This is not an officially supported Google product. This project is not eligible for the [Google Open Source Software Vulnerability Rewards Program](https://bughunters.google.com/open-source-security).

This project is intended for demonstration purposes only. It is not intended for use in a production environment.

