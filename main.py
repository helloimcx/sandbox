from fastapi import FastAPI, HTTPException, Request
import asyncio
from jupyter_client import AsyncKernelManager
import json
from asyncio import TimeoutError
import tempfile
import os
import shutil
import base64
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
import httpx

app = FastAPI()

class ExecuteRequest(BaseModel):
    code: str
    file_urls: Optional[List[HttpUrl]] = None

async def download_file(url: HttpUrl, dest_folder: str):
    """异步下载单个文件"""
    filename = os.path.basename(str(url))
    file_path = os.path.join(dest_folder, filename)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(str(url), follow_redirects=True, timeout=30.0)
            response.raise_for_status()  # 如果下载失败则抛出异常
            with open(file_path, "wb") as f:
                f.write(response.content)
            return filename
        except httpx.RequestError as e:
            return f"Failed to download {url}: {e}"

@app.post("/execute")
async def execute_code(request: ExecuteRequest):
    temp_dir = tempfile.mkdtemp()

    try:
        # 从URL下载文件
        if request.file_urls:
            download_tasks = [download_file(url, temp_dir) for url in request.file_urls]
            results = await asyncio.gather(*download_tasks)
            for result in results:
                if isinstance(result, str) and result.startswith("Failed"): # 检查下载错误
                    raise HTTPException(status_code=400, detail=result)

        files_before = set(os.listdir(temp_dir))

        execution_code = f"import os; os.chdir(r'{temp_dir}')\n{request.code}"

        km = AsyncKernelManager(kernel_name="python3")
        await km.start_kernel()

        output = []
        try:
            client = km.client()
            client.start_channels()
            msg_id = client.execute(execution_code)

            async with asyncio.timeout(60):
                while True:
                    try:
                        msg = await asyncio.wait_for(client.get_iopub_msg(), timeout=30)
                        if msg['parent_header'].get('msg_id') == msg_id:
                            msg_type = msg['msg_type']
                            if msg_type == 'execute_result':
                                output.append(msg['content']['data'])
                            elif msg_type == 'stream':
                                output.append(msg['content']['text'])
                            elif msg_type == 'error':
                                output.append(msg['content']['traceback'])
                            elif msg_type == 'status' and msg['content']['execution_state'] == 'idle':
                                break
                    except asyncio.TimeoutError:
                        output.append("Timeout waiting for kernel message.")
                        break
        except asyncio.TimeoutError:
            output.append("Total execution time exceeded 60s.")
        finally:
            await km.shutdown_kernel(now=True)

        files_after = set(os.listdir(temp_dir))
        new_files = files_after - files_before

        output_files = {}
        for filename in new_files:
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    encoded_content = base64.b64encode(f.read()).decode('utf-8')
                    output_files[filename] = encoded_content

    finally:
        shutil.rmtree(temp_dir)

    return {"result": output, "files": output_files}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)