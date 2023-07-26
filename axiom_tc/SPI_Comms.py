import spidev
from time              import sleep

class SPI_Comms:
    def __init__(self, bus, device):
        self.__spi = spidev.SpiDev()
        self.__spi.open(bus, device)

        # Configure SPI bus, less than 7MHz will work
        self.__spi.max_speed_hz = 7000000
        self.__spi.mode = 0

    def comms_init(self, axiom):
        self.__axiom = axiom

    def read_page(self, target_address, length):
        ta_msb = (target_address & 0xFF00) >> 8
        ta_lsb = (target_address & 0x00FF)

        length_msb = (length & 0x7F00) >> 8
        length_lsb = (length & 0x00FF)

        length_msb |= 0x80 # Set the READ bit

        spi_header  = [ta_lsb, ta_msb, length_lsb, length_msb]
        spi_padding = [0x00] * 32
        spi_body    = [0x00] * length
        spi_op      = spi_header + spi_padding + spi_body
        self.__spi.xfer(spi_op)
        sleep(0.001)
        return spi_op[36:]


    def write_page(self, target_address, length, payload):
        if length > len(payload):
            print("ERROR: Asked to write more bytes than available in payload: ")
            print("Length: %d, and given payload is %d" % (length,len(payload)))
            raise AssertionError

        ta_msb = (target_address & 0xFF00) >> 8
        ta_lsb = (target_address & 0x00FF)

        length_msb = (length & 0x7F00) >> 8
        length_lsb = (length & 0x00FF)

        length_msb &= ~0x80 # Ensure the read bit is clear

        spi_header  = [ta_lsb, ta_msb, length_lsb, length_msb]
        spi_padding = [0x00] * 32
        spi_body    = payload
        spi_op      = spi_header + spi_padding + spi_body
        self.__spi.xfer(spi_op)
        sleep(0.001)


    def close(self):
        self.__spi.close()
