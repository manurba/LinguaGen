import aiohttp
import asyncio
import logging
import time
from dataclasses import (
    dataclass,
    field,
)
from aiohttp import FormData

async def text_from_audio(
        request_url: str,
        request_header: dict,
        file_path: str,
        model: str,
    ):
    form = FormData()
    form.add_field('model', model)
    # Open the file in binary mode and add it to the form
    form.add_field('file', file_path, filename="audio.mp3")

    async with aiohttp.ClientSession() as session:
        # Note that headers are not manually set here; aiohttp will set the appropriate multipart/form-data headers.
        async with session.post(url=request_url, headers=request_header, data=form) as response:
            response_data = await response.json()
            return response_data

async def text_to_audio(
        request_url: str,
        request_header: dict,
        voice: str,
        input: str,
        model: str,
    ):
    
    data = {
        "model": model,
        "input": input,
        "voice": voice
    }
    async with aiohttp.ClientSession() as session:
        # Note that headers are not manually set here; aiohttp will set the appropriate multipart/form-data headers.
        async with session.post(url=request_url, headers=request_header, json=data) as response:
            response_data = await response.read()
            return response_data

@dataclass
class StatusTracker:
    """Stores metadata about the script's progress. Only one instance is created."""

    num_tasks_started: int = 0
    num_tasks_in_progress: int = 0  # script ends when this reaches 0
    num_tasks_succeeded: int = 0
    num_tasks_failed: int = 0
    num_rate_limit_errors: int = 0
    num_api_errors: int = 0  # excluding rate limit errors, counted above
    num_other_errors: int = 0
    time_of_last_rate_limit_error: int = 0  # used to cool off after hitting rate limits


@dataclass
class APIRequest:
    """Stores an API request's inputs, outputs, and other metadata. Contains a method to make an API call."""

    task_id: int
    request_json: dict
    token_consumption: int
    attempts_left: int
    metadata: dict
    result: list = field(default_factory=list)

    results_dict = {}
    lock = asyncio.Lock()

    async def call_api(
        self,
        session: aiohttp.ClientSession,
        request_url: str,
        api_endpoint: str,
        request_header: dict,
        retry_queue: asyncio.Queue,
        status_tracker: StatusTracker,
    ):
        """Calls the OpenAI API and saves results."""
        logging.info(f"Starting request #{self.task_id}")
        error = None
        try:
            async with session.post(
                url=request_url, headers=request_header, json=self.request_json
            ) as response:
                response = await response.json()
            if "error" in response:
                logging.warning(
                    f"Request {self.task_id} failed with error {response['error']}"
                )
                status_tracker.num_api_errors += 1
                error = response
                if "Rate limit" in response["error"].get("message", ""):
                    status_tracker.time_of_last_rate_limit_error = time.time()
                    status_tracker.num_rate_limit_errors += 1
                    status_tracker.num_api_errors -= (
                        1  # rate limit errors are counted separately
                    )

        except (
            Exception
        ) as e:  # catching naked exceptions is bad practice, but in this case we'll log & save them
            logging.warning(f"Request {self.task_id} failed with Exception {e}")
            status_tracker.num_other_errors += 1
            error = e
        if error:
            self.result.append(error)
            if self.attempts_left:
                retry_queue.put_nowait(self)
            else:
                logging.error(
                    f"Request {self.request_json} failed after all attempts. Saving errors: {self.result}"
                )
                data = (
                    [self.request_json, [str(e) for e in self.result], self.metadata]
                    if self.metadata
                    else [self.request_json, [str(e) for e in self.result]]
                )

                status_tracker.num_tasks_in_progress -= 1
                status_tracker.num_tasks_failed += 1

                async with self.lock:
                    self.results_dict[self.task_id] = {
                        "request": self.request_json,
                        "response": response,
                        "errors_flag": True,
                    }
        else:
            data = (
                [self.request_json, response, self.metadata]
                if self.metadata
                else [self.request_json, response]
            )
            status_tracker.num_tasks_in_progress -= 1
            status_tracker.num_tasks_succeeded += 1

            if api_endpoint.endswith("completions"):
                async with self.lock:
                    self.results_dict[self.task_id] = {
                        "request": self.request_json,
                        "response": response.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content"),
                        "errors_flag": False,
                    }
            else:
                raise NotImplementedError(
                    f'API endpoint "{self.api_endpoint}" not implemented in this script'
                )
            logging.debug(f"Request {self.task_id} done")
