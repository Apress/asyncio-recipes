import asyncio
import functools
import os
import signal

SIGNAL_NAMES = ('SIGINT', 'SIGTERM')
SIGNAL_NAME_MESSAGE = " or ".join(SIGNAL_NAMES)


def sigint_handler(signame, *, loop, ):
    print(f"Stopped loop because of {signame}")
    loop.stop()


def sigterm_handler(signame, *, loop, ):
    print(f"Stopped loop because of {signame}")
    loop.stop()


loop = asyncio.get_event_loop()

for signame in SIGNAL_NAMES:
    loop.add_signal_handler(getattr(signal, signame),
                            functools.partial(locals()[f"{signame.lower()}_handler"], signame, loop=loop))

print("Event loop running forever, press Ctrl+C to interrupt.")
print(f"pid {os.getpid()}: send {SIGNAL_NAME_MESSAGE} to exit.")
try:
    loop.run_forever()
finally:
    loop.close()  # optional
