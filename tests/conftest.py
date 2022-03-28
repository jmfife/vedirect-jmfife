from pytest import fixture
from unittest.mock import patch, Mock
import dummyserial
import logging
import sys
from serial import SerialBase
import asyncio
import pytest_asyncio

# noinspection PyUnresolvedReferences
import serial

# logging.basicConfig(level=logging.DEBUG)


@fixture(scope="function")
def fake_serial():
    dummy = dummyserial.Serial(port="COM50", baudrate=9600)
    dummy.flushInput = Mock()
    dummy.reset_input_buffer = Mock()
    dummy._logger.setLevel(logging.INFO)
    with patch("serial.Serial", spec=SerialBase) as mock:
        # All possible parameters
        mock.return_value = dummy
        yield dummy


@pytest_asyncio.fixture(scope="function")
async def fake_async_serial():
    fake_stream = asyncio.streams.StreamReader()
    with patch("asyncio.StreamReader", spec=asyncio.streams.StreamReader) as mock:
        # All possible parameters
        mock.return_value = fake_stream
        yield fake_stream


@fixture(scope="module")
def fake_micropython():
    original_modules = sys.modules
    original_modules["uasyncio"] = asyncio
    # monkeypatch.setattr(sys, "modules", original_modules)
    with patch(
        "vedirect.vedirect.MICROPYTHON", spec=bool
    ) as mock_micropython, patch.object(sys, "modules", new=original_modules):
        mock_micropython = True
        yield
