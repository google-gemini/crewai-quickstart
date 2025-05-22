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

mport os
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

MODEL = 'gemini/gemini-2.5-flash-preview-04-17'


class GeminiWithGoogleSearch(LLM):
    """A Gemini-specific LLM that has the 'google_search' tool enabled.

    This tool has some quota included on the "free tier" of the API, so you
    can use Google Search as a tool in your app without needing an additional
    service.

    Be sure to read the docs on using the Google Search grounding tool at
    https://ai.google.dev/gemini-api/docs/grounding.
    """

    def __init__(self, model: str | None = None, **kwargs):
       if not model:
          # Use a default Gemini model.
          model = os.getenv('MODEL', 'gemini/gemini-2.5-flash-preview-04-17')

       super().__init__(model, **kwargs)

    def call(
        self,
        messages: str | list[dict[str, str]],
        tools: list[dict] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
    ) -> str | Any:
        if not tools:
            tools = []

        # LiteLLM will throw a warning if it sees `google_search`, so use camel case here.
        tools.insert(0, {'googleSearch': {}})

        return super().call(
            messages=messages,
            tools=tools,
            callbacks=callbacks,
            available_functions=available_functions
        )


@CrewBase
class GithubResumeGenerator:
    """GithubResumeGenerator crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def github_profile_researcher(self) -> Agent:
        gemini_with_search = GeminiWithGoogleSearch(model=MODEL)
        return Agent(
            config=self.agents_config['github_profile_researcher'],
            llm=gemini_with_search,
            verbose=True,
        )
    
    @agent
    def resume_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_writer'],
            verbose=True,
            llm=MODEL,
        )

    @task
    def profile_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['profile_research_task'],
        )

    @task
    def resume_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['resume_generation_task'],
            # output_file='resume.md' # Optional: define output file for the resume
        )

    @crew
    def crew(self, **kwargs) -> Crew:
        """Creates the GithubResumeGenerator crew"""
        return Crew(
            agents=self.agents,  # type: ignore[reportCallIssue]
            tasks=self.tasks, # type: ignore[reportCallIssue]
            process=Process.sequential,
            verbose=True,
            **kwargs,
        )
