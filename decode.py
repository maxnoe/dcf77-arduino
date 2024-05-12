import serial
from datetime import datetime
from argparse import ArgumentParser
from zoneinfo import ZoneInfo

CET = ZoneInfo("CET")

parser = ArgumentParser()
parser.add_argument("device")
parser.add_argument("-b", "--baud-rate", type=int, default=9600)


def bits(value, first, n_bits):
    return (value >> first) & ((1 << n_bits) - 1)


def bit(value, pos):
    return bool(value & (1 << pos))


def check_parity(value, first, n_bits, field):
    value = bits(value, first, n_bits)

    # dcf77 uses even parity
    if value.bit_count() % 2 != 0:
        raise ValueError(f"Field {field} failed parity check")


def decode(data):
    val = int(data, base=2)
    if bit(val, 0):
        raise ValueError("Bit 0 set, should always be 0")

    b = lambda first, n_bits: bits(val, first, n_bits)

    check_parity(val, 21, 8, "minute")
    minute = b(21,4) + 10 * b(25, 3)

    check_parity(val, 29, 7, "hour")
    hour = b(29, 4) + 10 * b(33, 2)

    check_parity(val, 36, 23, "date")
    day = b(36, 4) + 10 * b(40, 2)
    month = b(45, 4) + 10 * b(49, 1)
    year = 2000 + b(50, 4) + 10 * b(54, 4)

    cest = bit(val, 17)
    cet = bit(val, 18)
    if cest and cet:
        raise ValueError("CEST and CET bit set")

    timezone = "CET" if cet else "CEST"

    if not bit(val, 20):
        raise ValueError("Bit 20 not set, should always be 1")

    return {
        "time": datetime(year, month, day, hour, minute, tzinfo=CET),
        "timezone": timezone,
        "call_bit": bit(val, 15),
        "dst_switch": bit(val, 16),
        "imminent_leap_second": bit(val, 19)
    }


def main(args=None):
    args = parser.parse_args(args)

    with serial.Serial(args.device, args.baud_rate, timeout=3) as dev:
        while True:
            line = dev.readline().decode().strip()

            # timeout
            if not line:
                continue

            print(line)
            if line.startswith("data:"):
                data = decode(line.removeprefix("data:"))
                time = data.pop("time")
                print(time.isoformat(), data)


def test_decode():
    line = "10010010000101111010010000100101010110100100001101010011010"
    expected = datetime.fromisoformat("2024-05-12T09:56:00+02:00")

    result = decode(line)
    assert result["time"] == expected


def test_broken():
    from pytest import raises

    line = "10010010000101111010010000100101010100100100001101010011010"
    with raises(ValueError, match="Field minute"):
        decode(line)

    line = "10010010000101111010010000110101010110100100001101010011010"
    with raises(ValueError, match="Field hour"):
        decode(line)

    line = "10010000000101111010010000100101010110100100001101010011010"
    with raises(ValueError, match="Field date"):
        decode(line)


if __name__ == "__main__":
    main()
