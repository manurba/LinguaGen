import aiohttp
import asyncio
import os
import time
import logging
from dotenv import load_dotenv

from lingua.utils.dataclasses import (
    StatusTracker,
    APIRequest
)
from lingua.utils.functions import (
    api_endpoint_from_url,
    num_tokens_consumed_from_request,
    task_id_generator_function
)


class LinguaGen:
    def __init__(self) -> None:
        self._get_secrets()
        self._get_header()
        self.api_endpoint = api_endpoint_from_url("https://api.openai.com/v1/chat/completions")
    
    def _get_secrets(self):
        load_dotenv()

    def _get_header(self):
        self.request_header = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}

    async def request_handler(
        self,
        request_json,
        request_url,
        max_requests_per_minute,
        max_tokens_per_minute,
        token_encoding_name,
        max_attempts,
    ):
        seconds_to_pause_after_rate_limit_error = 15
        seconds_to_sleep_each_loop = (
            0.001  # 1 ms limits max throughput to 1,000 requests per second
        )

        queue_of_requests_to_retry = asyncio.Queue()
        task_id_generator = (
            task_id_generator_function()
        )
        status_tracker = (
            StatusTracker()
        )
        next_request = None

        available_request_capacity = max_requests_per_minute
        available_token_capacity = max_tokens_per_minute
        last_update_time = time.time()

        api_endpoint = api_endpoint_from_url(request_url)

        # initialize flags
        queue_not_finished = True  # after queue is empty, we'll skip it
        logging.debug(f"Initialization complete.")

        async with aiohttp.ClientSession() as session:
            while True:
                if next_request is None:
                    if not queue_of_requests_to_retry.empty():
                        next_request = queue_of_requests_to_retry.get_nowait()
                        logging.debug(
                            f"Retrying request {next_request.task_id}: {next_request}"
                        )
                    elif queue_not_finished:
                        try:
                            next_request = APIRequest(
                                task_id=next(task_id_generator),
                                request_json=request_json,
                                token_consumption=num_tokens_consumed_from_request(
                                    request_json, api_endpoint, token_encoding_name
                                ),
                                attempts_left=max_attempts,
                                metadata=request_json.pop("metadata", None),
                            )
                            status_tracker.num_tasks_started += 1
                            status_tracker.num_tasks_in_progress += 1
                            logging.debug(
                                f"Reading request {next_request.task_id}: {next_request}"
                            )
                        except StopIteration:
                            # if file runs out, set flag to stop reading it
                            logging.debug("Read file exhausted")
                            file_not_finished = False
                # update available capacity
                current_time = time.time()
                seconds_since_update = current_time - last_update_time
                available_request_capacity = min(
                    available_request_capacity
                    + max_requests_per_minute * seconds_since_update / 60.0,
                    max_requests_per_minute,
                )
                available_token_capacity = min(
                    available_token_capacity
                    + max_tokens_per_minute * seconds_since_update / 60.0,
                    max_tokens_per_minute,
                )
                last_update_time = current_time

                # if enough capacity available, call API
                if next_request:
                    next_request_tokens = next_request.token_consumption
                    if (
                        available_request_capacity >= 1
                        and available_token_capacity >= next_request_tokens
                    ):
                        # update counters
                        available_request_capacity -= 1
                        available_token_capacity -= next_request_tokens
                        next_request.attempts_left -= 1

                        # call API
                        asyncio.create_task(
                            next_request.call_api(
                                session=session,
                                request_url=request_url,
                                request_header=self.request_header,
                                retry_queue=queue_of_requests_to_retry,
                                status_tracker=status_tracker,
                            )
                        )
                        next_request = None  # reset next_request to empty

                # if all tasks are finished, break
                if status_tracker.num_tasks_in_progress == 0:
                    break

                # main loop sleeps briefly so concurrent tasks can run
                await asyncio.sleep(seconds_to_sleep_each_loop)

                # if a rate limit error was hit recently, pause to cool down
                seconds_since_rate_limit_error = (
                    time.time() - status_tracker.time_of_last_rate_limit_error
                )
                if (
                    seconds_since_rate_limit_error
                    < seconds_to_pause_after_rate_limit_error
                ):
                    remaining_seconds_to_pause = (
                        seconds_to_pause_after_rate_limit_error
                        - seconds_since_rate_limit_error
                    )
                    await asyncio.sleep(remaining_seconds_to_pause)
                    # ^e.g., if pause is 15 seconds and final limit was hit 5 seconds ago
                    logging.warn(
                        f"Pausing to cool down until {time.ctime(status_tracker.time_of_last_rate_limit_error + seconds_to_pause_after_rate_limit_error)}"
                    )

async def main():
    lingua = LinguaGen()
    response = await lingua.request_handler(
        request_json={
            "model": "gpt-3.5-turbo-0125",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ],
            "max_tokens": 100,
        },
        request_url="https://api.openai.com/v1/chat/completions",
        max_requests_per_minute=200,
        max_tokens_per_minute=120_000,
        token_encoding_name="cl100k_base",
        max_attempts=5,
    )
    print(response)

if __name__ == '__main__':
    asyncio.run(main())