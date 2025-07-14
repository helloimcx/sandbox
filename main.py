from fastapi import FastAPI, HTTPException, Request
import asyncio
from jupyter_client import AsyncKernelManager
import json

app = FastAPI()

@app.post("/execute")
async def execute_code(request: Request):
    data = await request.json()
    code = data.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    # Start a new kernel
    km = AsyncKernelManager(kernel_name="python3")
    await km.start_kernel()

    try:
        # Execute the code
        client = km.client()
        client.start_channels()
        msg_id = client.execute(code)

        output = []
        while True:
            msg = await asyncio.wait_for(client.get_iopub_msg(), timeout=10)
            if msg['parent_header'].get('msg_id') == msg_id:
                if msg['msg_type'] == 'execute_result':
                    output.append(msg['content']['data'])
                elif msg['msg_type'] == 'stream':
                    output.append(msg['content']['text'])
                elif msg['msg_type'] == 'error':
                    output.append(msg['content']['traceback'])
                elif msg['msg_type'] == 'status' and msg['content']['execution_state'] == 'idle':
                    break
    finally:
        await km.shutdown_kernel(now=True)

    return {"result": output}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)