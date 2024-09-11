import asyncio
from functools import partial
import contextlib
from concurrent.futures import ThreadPoolExecutor
from serial import serial_for_url,Serial
from typing import Optional,Union,Literal,AsyncGenerator


Timeoutproperties=Union[Literal['write_timeout'],Literal['timeout']]


class serialAsync:

    @classmethod
    async def create(
        cls,
        port: str,
        baud_rate: int,
        time_out: Optional[float] = None,
        write_timeout:Optional[float]=None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        buffer_reset_before_write:bool=False,
    ) -> 'serialAsync':
        loop = loop or asyncio.get_running_loop()
        executor=ThreadPoolExecutor(max_workers=1)
        serial = await loop.run_in_executor(
            executor=executor,
            func=partial(
                serial_for_url,
                url=port,
                baudrate=baud_rate,
                timeout=time_out,
                write_timeout=write_timeout,
            )
        )
        return cls(
            serial=serial,
            executor=executor,
            loop=loop,
            buffer_reset_before_write=buffer_reset_before_write
        )
    
    def __init__(
        self,
        serial:Serial,
        executor:ThreadPoolExecutor,
        loop:asyncio.AbstractEventLoop,
        buffer_reset_before_write:bool,
    )->None:
        self._serial=serial
        self._executor=executor
        self._loop=loop
        self._buffer_reset_before_write=buffer_reset_before_write

    async def read_until(
            self,
            match:bytes,
    )->bytes:
        return await self._loop.run_in_executor(
            executor=self._executor,
            func=partial(
                self._serial.read_until,expected=match
            )
        )
    
    async def write(
            self,
            data:bytes
    )->None:
         
        await self._loop.run_in_executor(
        executor=self._executor,
        func=partial(self._sync_write,data=data)
        )
    def _sync_write(
            self,
            data:bytes
    )->None:
        if self._buffer_reset_before_write:
            self._serial.reset_input_buffer()
        self._serial.write(data=data)
        self._serial.flush()

    async def open(self)->None:
        return await self._loop.run_in_executor(
            executor=self._executor,func=self._serial.open
        )
    
    async def close(self)->None:
        return await self._loop.run_in_executor(
            executor=self._executor,func=self._serial.close
        )
    
    async def is_open(self)->bool:

        return self._serial.is_open is True    
        
    def reset_input_buffer(self)->None:
        return self._serial.reset_input_buffer()

    @contextlib.asynccontextmanager
    async  def override_timeout(self,timeoutproperty:Timeoutproperties,timeout:Optional[float])->AsyncGenerator[None,None]:
        default_timeout=getattr(self._serial,timeoutproperty)
        override= timeout is not None and default_timeout!=timeout       
        try:
            if override: 
                await self._loop.run_in_executor(
                executor=self._executor,
                func= lambda: setattr(self._serial,timeoutproperty,timeout),
                )
            yield
        finally:
            if override:
                await self._loop.run_in_executor(
                    executor=self._executor,
                    func=lambda:setattr(self._serial,timeoutproperty,default_timeout),
                )
            
if __name__ == '__main__':
    import asyncio
    import time

async def main():
    loop = asyncio.get_running_loop()
    serial = await serialAsync.create(
        port='/dev/pts/7',  # Use one of the socat ports here
        baud_rate=9600,
        time_out=1.0,
        write_timeout=1.0,
        buffer_reset_before_write=True,
        loop=loop
    )
    cerial=await serialAsync.create(
        port='/dev/pts/8',
        baud_rate=100000,
        time_out=1.0,
        write_timeout=1.0,
        buffer_reset_before_write=True,
        loop=loop
    )
    try:
        print("Waiting for data...")
        while True:
            print(f"{time.time():.2f} - serial sent yooo")
            await serial.write(b'technoculture')
            port1_response = await cerial.read_until(b'\n')
            print(f"{time.time():.2f} - cerial sent noooooo")
            await cerial.write(b'vastuvihar')
            response = await serial.read_until(b'\n')
            
            if port1_response:
                print(f"{time.time():.2f} - Received from cerial: {port1_response.decode().strip()}")
            else:
                print(f"{time.time():.2f} - No data received from cerial (timeout)")
            
            if response:
                print(f"{time.time():.2f} - Received from serial: {response.decode().strip()}")
            else:
                print(f"{time.time():.2f} - No data received from serial (timeout)")
    except asyncio.CancelledError:
        print("Operation cancelled")
    finally:
        await serial.close()
        await cerial.close()

# Run the main coroutine
asyncio.run(main())
    # Run the main coroutine1