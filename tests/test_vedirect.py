from vedirect import VEDirect
from vedirect_device_emulator import VEDirectDeviceEmulator


def test_basic(fake_serial):
    emu = VEDirectDeviceEmulator(fake_serial, model="BMV_700")
    resp = emu.get_bytes()
    record = VEDirect.typecast(
        emu.get_record()
    )  # Get epxected response, typecast since emu does not do this
    # Write emulated data into serial read queue
    fake_serial._waiting_data = resp
    # Create VE direct object with obviously bad port
    ve = VEDirect("BADPORT")
    res = ve.read_data_single()

    assert record == res
