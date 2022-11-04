#! /usr/bin/env python3
from pathlib import Path

import appdirs
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi_versioning import VersionedFastAPI, version
from loguru import logger
from gpiozero import Servo

from pydantic import BaseModel

import asyncio
import json
import os
import time
from typing import Any, Dict, Optional
import sys

import aiohttp


class TextData(BaseModel):
    data: str


SERVICE_NAME = "Sensor2Mavlink"

app = FastAPI(
    title="Sensor2Mavlink",
    description="API to send Sensors to Mavlink",
)

logger.info(f"Starting {SERVICE_NAME}!")

servos = {}

@app.post("/setServo", status_code=status.HTTP_200_OK)
@version(1, 0)
async def set_servo(pin: int, pwm: float) -> Any:
    if pin < 0 or pwm < -1 or pwm > 1:
        raise HTTPException("Invalid values")
    if pin not in servos:
        servos[pin] = Servo(pin)
    servos[pin].value = pwm
    test=MM()
    test.send_statustext(str("Hallo"))
    return "ok"

app = VersionedFastAPI(app, version="1.0.0", prefix_format="/v{major}.{minor}", enable_latest=True)

app.mount("/", StaticFiles(directory="static",html = True), name="static")

@app.get("/", response_class=FileResponse)
async def root() -> Any:
        return "index.html"

if __name__ == "__main__":
    # Running uvicorn with log disabled so loguru can handle it
    uvicorn.run(app, host="0.0.0.0", port=8120, log_config=None)
    
    
class MM:
    def __init__(self) -> None:

        self.time_since_boot = time.time()
        self.m2r_address = "http://localhost:6040/mavlink"
        self.request_timeout = 1.0
        self.mavlink2rest_package = {
            "header": {"system_id": 1, "component_id": 1, "sequence": 9},
            "message": {"chunk_seq": 0,
            "id": 0,
            "severity": { "type": "MAV_SEVERITY_EMERGENCY" },
            "text": [ "H", "a", "l", "l", "o", " ", "D", "A", "V", "I", "D", " ", " ", " ", " ", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000", "\u0000" ],
            "type": "STATUSTEXT"
            },
        }
    def send_statustext(self, message: str) -> None:
    
        lst = []

        for i in message:
            lst.append(i)
        self.mavlink2rest_package = {
            "header": {"system_id": 1, "component_id": 1, "sequence": 1},
            "message": {"chunk_seq": 0,
            "id": 0,
            "severity": { "type": "MAV_SEVERITY_EMERGENCY" },
            "text": lst,
            "type": "STATUSTEXT"
            },
        }
        asyncio.run(self.send_mavlink_message(1))
    def send_ph(self, ph: float) -> None:
        self.mavlink2rest_package = {
            "header": {"system_id": 1, "component_id": 1, "sequence": 1},
            "message": {"time_usec": ((time.time() - self.time_since_boot) * 1000),
            "ph": float(ph),
            "type": "SENSOR_PH"
            },
        }
        asyncio.run(self.send_mavlink_message(1))  

    async def send_mavlink_message(self, port: int) -> None:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                     self.m2r_address, data=json.dumps(self.mavlink2rest_package), timeout=self.request_timeout
                ) as response:
                    print(f"Received status code of {response.status}.")
                    if not response.status == 200:
                        print(f"Received status code of {response.status}.")
            except asyncio.exceptions.TimeoutError as error:
                print(f"Request timed out after {request_timeout} second.") 
                await asyncio.sleep(1)
