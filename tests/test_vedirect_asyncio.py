import pytest
from async_timeout import timeout
import asyncio.streams
from vedirect_device_emulator import VEDirectDeviceEmulator


@pytest.mark.asyncio
async def test_vedirect_asyncio(
    fake_micropython, fake_serial, fake_async_serial: asyncio.streams.StreamReader
):
    # Lazy import to allow fixture to mock MICROPYTHON
    from vedirect.vedirect_asyncio import VEDirectAsyncio

    async with timeout(50.0):
        str_var = ""
        emu = VEDirectDeviceEmulator(str_var, model="BMV_700")
        resp = emu.get_bytes()
        record = VEDirectAsyncio.typecast(
            emu.get_record()
        )  # Get epxected response, typecast since emu does not do this
        # Write emulated data into serial read queue
        # Create VE direct object with obviously bad port
        ve = VEDirectAsyncio(fake_serial)
        fake_async_serial.feed_data(resp)
        res = await ve.read_data_single()
        assert record == res
