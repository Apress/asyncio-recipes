import asyncio
try:
    loop = asyncio.get_running_loop()

except RuntimeError:
    print("No loop running")
