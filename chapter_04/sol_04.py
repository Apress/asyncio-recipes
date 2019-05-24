import asyncio
import enum
import logging
import sys
from dataclasses import dataclass


class State(enum.Enum):
    IDLE = enum.auto()
    STARTED = enum.auto()
    PAUSED = enum.auto()


@dataclass(frozen=True)
class Event:
    name: str


START = Event("Start")
PAUSE = Event("Pause")
STOP = Event("Stop")
EXIT = Event("Exit")

STATES = (START, PAUSE, STOP, EXIT)
CHOICES = "\n".join([f"{i}: {state.name}" for i, state in enumerate(STATES)])

MENU = f"""
Menu

Enter your choice:

{CHOICES}

"""

TRANSITIONS = {
    (State.IDLE, PAUSE): State.IDLE,
    (State.IDLE, START): State.STARTED,
    (State.IDLE, STOP): State.IDLE,

    (State.STARTED, START): State.STARTED,
    (State.STARTED, PAUSE): State.PAUSED,
    (State.STARTED, STOP): State.IDLE,

    (State.PAUSED, START): State.STARTED,
    (State.PAUSED, PAUSE): State.PAUSED,
    (State.PAUSED, STOP): State.IDLE,

    (State.IDLE, EXIT): State.IDLE,
    (State.STARTED, EXIT): State.IDLE,
    (State.PAUSED, EXIT): State.IDLE,
}


class StateMachineException(Exception):
    pass


class StartStateMachineException(StateMachineException):
    pass


class StopStateMachineException(StateMachineException):
    pass


async def next_state(state_machine, event, *, exc=StateMachineException):
    try:
        if state_machine:
            await state_machine.asend(event)
    except StopAsyncIteration:
        if exc != StopStateMachineException:
            raise exc()
    except:
        raise exc()


async def start_statemachine(state_machine, ):
    await next_state(state_machine, None, exc=StartStateMachineException)


async def stop_statemachine(state_machine, ):
    await next_state(state_machine, EXIT, exc=StopStateMachineException)


async def create_state_machine(transitions, *, logger=None, ):
    if not logger:
        logger = logging.getLogger(__name__)
    event, current_state = None, State.IDLE
    while event != EXIT:

        event = yield

        edge = (current_state, event)

        if edge not in transitions:
            logger.error("Cannot consume %s in state %s", event.name, current_state.name)
            continue

        next_state = transitions.get(edge)
        logger.debug("Transitioning from %s to %s", current_state.name, next_state.name)
        current_state = next_state


def pick_next_event(logger):
    next_state = None

    while not next_state:
        try:
            next_state = STATES[int(input(MENU))]
        except (ValueError, IndexError):
            logger.error("Please enter a valid choice!")
            continue

    return next_state


async def main(logger):
    state_machine = create_state_machine(TRANSITIONS, logger=logger)

    try:
        await start_statemachine(state_machine)

        while True:
            event = pick_next_event(logger)
            if event != EXIT:
                await next_state(state_machine, event)
            else:
                await stop_statemachine(state_machine)

    except StartStateMachineException:
        logger.error("Starting the statemachine was unsuccessful")
    except StopStateMachineException:
        logger.error("Stopping the statemachine was unsuccessful")
    except StateMachineException:
        logger.error("Transitioning the statemachine was unsuccessful")


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)

try:
    asyncio.get_event_loop().run_until_complete(main(logger))
except KeyboardInterrupt:
    logger.info("Closed loop..")