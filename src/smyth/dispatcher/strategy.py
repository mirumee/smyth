import logging
from abc import ABC, abstractmethod

from smyth.dispatcher.process import LambdaProcess

LOGGER = logging.getLogger(__name__)


class BaseDispatchStrategy(ABC):
    name: str

    def __init__(self, process_groups: dict[str, list[LambdaProcess]]):
        self.process_groups = process_groups

    @abstractmethod
    def get_process(self, process_definition_name: str) -> LambdaProcess | None:
        raise NotImplementedError("get_process method must be implemented")


class FirstWarmDispatchStrategy(BaseDispatchStrategy):
    """This strategy prioritizes the use of the first available Lambda Process 
    in a "warm" state to handle incoming requests. If no warm instances are 
    available, it initiates a "cold start". This behavior more closely mimics 
    the operational dynamics of AWS Lambda, where reusing warm instances can 
    lead to faster response times."""
    
    name: str = "first_warm"

    def get_process(self, process_definition_name: str) -> LambdaProcess | None:
        # Look for an available, warm process
        # If no warm process is available, look for a cold process and start it
        best_candidate = None
        for process in self.process_groups[process_definition_name]:
            if process.state == "WARM":
                # If we find a warm process, return it immediately
                return process
            if process.state == "COLD" and not best_candidate:
                # If we find a cold process, store it as a candidate and
                # look for another warm process
                best_candidate = process

        return best_candidate


class RoundRobinDispatchStrategy(BaseDispatchStrategy):
    """This strategy, not typical for AWS Lambda's behavior, is beneficial 
    during development. It rotates among Lambda Processes for each request, 
    given that concurrency is set higher than `1`. This approach encourages 
    developers to avoid relying on global state across requests, promoting 
    best practices in serverless application design."""

    name: str = "round_robin"

    def get_process(self, process_definition_name: str) -> LambdaProcess | None:
        return sorted(
            self.process_groups[process_definition_name],
            key=lambda process: process.last_used_timestamp,
        )[0]
