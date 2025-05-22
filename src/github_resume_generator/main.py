#!/usr/bin/env python
import json
import pathlib
import sys

from github_resume_generator.crew import GithubResumeGenerator


def run(username: str = ''):
    """
    Run the crew.
    """
    if not username:
        username = sys.argv[1]
    if not username:
        # I volunteer as tribute.
        username = 'markmcd'

    inputs = {
        'username': username,
    }
    
    try:
        result = GithubResumeGenerator().crew().kickoff(inputs=inputs)

        # Save the results.
        md_file = pathlib.Path(f'{username}_resume.md')
        md_file.write_text(result.raw)
        full_output = pathlib.Path(f'{username}_resume.json')
        full_output.write_text(json.dumps(
            [t.model_dump(exclude_none=True) for t in result.tasks_output]))

    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'username': 'markmcd',
    }
    try:
        GithubResumeGenerator().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        GithubResumeGenerator().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'username': 'markmcd',
    }

    try:
        GithubResumeGenerator().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == '__main__':
    run(sys.argv[1])
