from .vedirect import MICROPYTHON
from .vedirect import VEDirect as _VEDirect

if not MICROPYTHON:
    raise NotImplementedError("This is only for Micropython")
else:
    import uasyncio as asyncio


class VEDirectAsyncio(_VEDirect):
    """An asyncio implementation of a VEDirect interface"""

    def __init__(self, serialport, timeout=60):
        super().__init__(serialport, timeout)
        self.stream_reader = asyncio.StreamReader(self.ser)
        self.timeout_s = timeout

    async def read_data_single(self):
        """Await a single VEDirect record indefinitely"""
        while True:
            byte = await self.stream_reader.read(1)
            if byte:
                record = self._input(byte)
                if record is not None:
                    return self.typecast(record)

    async def read(self):
        """In asyncio, this is the main interface function to read a record from VEDirect.

        It will await a record until a complete record is received OR self.timeout is reached.
        If it timesout, a TimeoutError will be raised.
        """
        return await asyncio.wait_for(self.read_data_single(), timeout=self.timeout_s)
