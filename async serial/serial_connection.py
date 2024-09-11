from typing import Optional
from async_serial import serialAsync
import logging 
from asyncio import AbstractEventLoop
import asyncio
from errors import ErrorResponse,NoResponse,AlarmResponse
log =logging.getLogger(__name__)

class serialconnection:

    @classmethod
    async def build_serial(cls,port:str,baudrate:int,timeout:float,loop:Optional[AbstractEventLoop],buffer_reset_before_write:bool)->serialAsync:
        return await serialAsync(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            loop=loop,
            buffer_reset_before_write=buffer_reset_before_write,
        )
    @classmethod
    async def create(cls,port:str,baudrate:int,timeout:float,ack:str,name:Optional[str]=None,retry_wait_time_seconds:float=0.1,loop:Optional[AbstractEventLoop]=None,error_keyword:Optional[str]=None,alarm_keyword:Optional[str]=None,buffer_reset_before_write:bool=False)->'serialconnection':
        serial=await cls.build_serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            loop=loop,
            buffer_reset_before_write=buffer_reset_before_write
        )
        return cls(
            serial=serial,
            port=port,
            name=name,
            ack=ack,
            retry_wait_time_seconds=retry_wait_time_seconds,
            error_keyword=error_keyword or "error",
            alarm_keyword=alarm_keyword or "alarm"
        )
    def __init__(self,serial: serialAsync,
        port: str,
        name: str,
        ack: str,
        retry_wait_time_seconds: float,
        error_keyword: str,
        alarm_keyword: str,) -> None:
        self._serial = serial
        self._port = port
        self._name = name
        self._ack = ack.encode()
        self._retry_wait_time_seconds = retry_wait_time_seconds
        self._send_data_lock = asyncio.Lock()
        self._error_keyword = error_keyword.lower()
        self._alarm_keyword = alarm_keyword.lower()

    async def send_command(self,command:CommandBuilder,retries:int=0,timeout:Optional[float]=None)->str:
        return await self.send_data(
            data=command.build(),retries=retries,timeout=timeout
        )
    async def send_dfu_command(self,command:CommandBuilder)->None:
        encoded_command=command.build().encode()

        async with self._send_data_lock:
            log.debug(f"{self.name}:Write->{encoded_command}")
            await self._serial.write(data=encoded_command)
    
    async def send_data(
            self,data:str,retries:int=0,timeout:Optional[float]=None
    )->str:
            async with self._send_data_lock, self._serial.timeout_override(
            "timeout", timeout
        ):
                return await self._send_data(data=data, retries=retries)        

    async def _send_data(self,data:str,retries:int=0)->str:
        data_encode=data.encode()
        for retry in range(retries + 1):
            log.debug(f"{self.name}: Write -> {data_encode!r}")
            await self._serial.write(data=data_encode)

            response = await self._serial.read_until(match=self._ack)
            log.debug(f"{self.name}: Read <- {response!r}")

            if (
                self._ack in response
                or self._error_keyword.encode() in response.lower()
            ):
                # Remove ack from response
                response = response.replace(self._ack, b"")
                str_response = self.process_raw_response(
                    command=data, response=response.decode()
                )
                self.raise_on_error(response=str_response)
                return str_response

            log.info(f"{self.name}: retry number {retry}/{retries}")

            await self.on_retry()

        raise NoResponse(port=self._port, command=data)
    
    async def open(self)->None:
        await self._serial.open()

    async def close(self)->None:
        await self._serial.close()
    
    async def is_open(self)->bool:
        return await self._serial.open()
    
    @property
    def port(self) -> str:
        return self._port

    @property
    def name(self) -> str:
        return self._name

    @property
    def send_data_lock(self) -> asyncio.Lock:
        return self._send_data_lock
    
    def raise_on_error(self,response:str)->None:

        lower=response.lower()
        if self._alarm_keyword in lower:
            raise AlarmResponse(port=self._port,response=response)
        
        if self._error_keyword in lower:
            raise ErrorResponse(port=self._port,response=response)
        
    async def on_retry(self)->None:

        await asyncio.sleep(self._retry_wait_time_seconds)
        await self._serial.close()
        await self._serial.open()

    def process_raw_response(self,command:str,response:str)->str:
        return response.strip()
    
class AsyncResponseSerialConnection(serialconnection):
    @classmethod
    async def create(cls,
        port: str,
        baud_rate: int,
        timeout: float,
        ack: str,
        name: Optional[str] = None,
        retry_wait_time_seconds: float = 0.1,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        error_keyword: Optional[str] = None,
        alarm_keyword: Optional[str] = None,
        reset_buffer_before_write: bool = False,
        async_error_ack: Optional[str] = None,
    ) -> 'AsyncResponseSerialConnection':
        
        serial = await super()._build_serial(
            port=port,
            baud_rate=baud_rate,
            timeout=timeout,
            loop=loop,
            reset_buffer_before_write=reset_buffer_before_write,
        )
        name = name or port
        return cls(
            serial=serial,
            port=port,
            name=name,
            ack=ack,
            retry_wait_time_seconds=retry_wait_time_seconds,
            error_keyword=error_keyword or "err",
            alarm_keyword=alarm_keyword or "alarm",
            async_error_ack=async_error_ack or "async",
        )
    def __init__(
        self,
        serial: serialAsync,
        port: str,
        name: str,
        ack: str,
        retry_wait_time_seconds: float,
        error_keyword: str,
        alarm_keyword: str,
        async_error_ack: str,
    ) -> None:
        super().__init__(
            serial=serial,
            port=port,
            name=name,
            ack=ack,
            retry_wait_time_seconds=retry_wait_time_seconds,
            error_keyword=error_keyword,
            alarm_keyword=alarm_keyword,
        )
        self._serial = serial
        self._port = port
        self._name = name
        self._ack = ack.encode()
        self._retry_wait_time_seconds = retry_wait_time_seconds
        self._error_keyword = error_keyword.lower()
        self._alarm_keyword = alarm_keyword.lower()
        self._async_error_ack = async_error_ack.lower()