import asyncio
import serial_asyncio
import sys
class AsyncSerial:
    def __init__(self, port, baudrate, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.reader = None
        self.writer = None

    async def connect(self):
        try:
            self.reader, self.writer = await serial_asyncio.open_serial_connection(
                url=self.port, baudrate=self.baudrate
            )
            print(f"Connected to {self.port} at {self.baudrate} baud.")
        except Exception as e:
            print(f"Failed to connect to {self.port}: {e}")
            await self.error_handler(e)

    async def disconnect(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            print(f"Disconnected from {self.port}.")

    async def send(self, data):
        if self.writer:
            self.writer.write(data.encode())
            await self.writer.drain()
            print(f"Sent: {data}")
        else:
            print("Writer is not connected.")

    async def receive(self, size=100):
        if self.reader:
            try:
                return await self.reader.read(size)
            except Exception as e:
                print(f"Error receiving data: {e}")
                await self.error_handler(e)
        return None
    
    async def error_handler(self, error):
        """Handle errors during communication."""
        print(f"Error occurred: {error}")


    def is_connected(self):
        return self.writer is not None and not self.writer.is_closing()

async def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <send_port> <receive_port>")
        return

    send_port = sys.argv[1]
    receive_port = sys.argv[2]

    # Create separate instances for sender and receiver
    sender = AsyncSerial(send_port, 9600)
    receiver = AsyncSerial(receive_port, 9600)

    try:
        # Connect to the serial ports
        await asyncio.gather(sender.connect(), receiver.connect())

        if sender.is_connected() and receiver.is_connected():
            print("Successfully connected to the serial ports.")
            
            # Send some data
            await sender.send("hello centrifuge")

            
            received_data = await receiver.receive()
            if received_data:
                print(f"Received data: {received_data.decode()}")
            else:
                print("No data received.")

            # Wait for a moment
            await asyncio.sleep(2)

            # Send another message
            await sender.send("How are you?")

            # Receive response
            received_data = await receiver.receive()
            if received_data:
                print(f"Received data: {received_data.decode()}")
            else:
                print("No data received.")

        else:
            print("Failed to connect to the serial ports.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Always disconnect, even if an error occurred
        await asyncio.gather(sender.disconnect(), receiver.disconnect())

if  __name__ =="__main__":
    asyncio.run(main())