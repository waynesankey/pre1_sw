from machine import Pin, I2C, SPI, UART
import json
import time
import uasyncio

from config import *
from modules.display import Display
from modules.encoder import Encoder_25LB22_Q
from modules.muses72320 import Muses72320
from modules.mute import Mute
from modules.nosensor import NoSensor
from modules.operate import Operate
from modules.mpc9808 import MPC9808
from modules.relay import Relay
from modules.selector import Selector
from modules.state import State
from modules.tube_timer import TubeTimer
from modules.volume import Volume
from lib.queue import Queue


# Declare Pins
vol0_in = Pin(5, Pin.IN, Pin.PULL_UP)
vol1_in = Pin(6, Pin.IN, Pin.PULL_UP)
volpb_in = Pin(7, Pin.IN, Pin.PULL_UP)
sel0_in = Pin(2, Pin.IN, Pin.PULL_UP)
sel1_in = Pin(3, Pin.IN, Pin.PULL_UP)
selpb_in = Pin(4, Pin.IN, Pin.PULL_UP)
mute_in = Pin(9, Pin.IN, Pin.PULL_UP)
operate_in = Pin(8, Pin.IN, Pin.PULL_UP)
led_red = Pin(25, Pin.OUT)


# Initialize hardware
i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=50_000)
spiVol = SPI(0, baudrate=100_000, polarity=1, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(18), mosi=Pin(19), miso=Pin(20))
spiCsVol = Pin(21, Pin.OUT)
spiRel = SPI(1, baudrate=200_000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(10), mosi=Pin(11), miso=Pin(12))
spiCsRel = Pin(13, Pin.OUT)
uart0 = UART(0, baudrate=115200, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17))

spiCsVol.value(1)
spiCsRel.value(0)


# Scan I2C
devices = i2c.scan()
if devices:
    for d in devices:
        if d == DISPLAY_ADDR:
            print("Found LCD display at address", hex(d))
        elif d == MPC9808_ADDR:
            print("Found MPC9808 temp sensor at address", hex(d))
        else:
            print("ERROR: Found I2C device at address", hex(d))
else:
    print("FAIL: no I2C devices found!!!")


# Initialize objects
vol_enc = Encoder_25LB22_Q(vol1_in, vol0_in)
sel_enc = Encoder_25LB22_Q(sel1_in, sel0_in)
dis = Display(i2c)
mus = Muses72320(spiVol, spiCsVol)
vol = Volume(dis, mus)
rel = Relay(spiRel, spiCsRel)
sel = Selector(vol, mus, dis, rel)
mut = Mute(mute_in, dis, vol, mus, rel, sel)
op = Operate(operate_in)
if ENABLE_TEMP_SENSOR:
    tmp = MPC9808(i2c, dis)
else:
    tmp = NoSensor()
    print("Temperature sensor disabled by ENABLE_TEMP_SENSOR flag")
tim = TubeTimer(dis)
st = State()
q = Queue(32)
persist_dirty = False
persist_due_ms = 0
last_temp_published = None

print("Vol0 Encoder Input pin 5:", vol0_in.value())
print("Vol1 Encoder Input pin 6:", vol1_in.value())
print("Sel0 Encoder Input pin 2:", sel0_in.value())
print("Sel1 Encoder Input pin 3:", sel1_in.value())


def load_persisted_state():
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            print("Loaded persisted state:", data)
            return data
    except (OSError, ValueError):
        return None


def apply_persisted_state(saved):
    if not saved:
        return
    vol.set_state(saved.get("volume", 0), saved.get("balance", 0))
    sel.set_select(saved.get("select", SELECT_DEFAULT))
    dis.set_brightness(saved.get("brightness", INITIAL_BRIGHTNESS))


def mark_persist_dirty():
    global persist_dirty, persist_due_ms
    persist_dirty = True
    persist_due_ms = time.ticks_add(time.ticks_ms(), STATE_WRITE_DELAY_MS)


def send_uart_line(line):
    uart0.write((line + "\n").encode("utf-8"))


def send_state_line():
    temp_value = getattr(tmp, "temperature", None)
    if temp_value is None:
        temp_field = "NA"
    else:
        temp_field = str(temp_value)
    line = (
        "STATE VOL=%d BAL=%d INP=%d MUTE=%d BRI=%d AMP=%d TEMP=%s"
        % (
            vol.get_current_volume(),
            vol.get_current_balance(),
            sel.get_current_select(),
            mut.get_mute_state(),
            dis.get_brightness(),
            st.state,
            temp_field,
        )
    )
    send_uart_line(line)


def send_tube_line(record):
    send_uart_line(
        "TUBE NUM=%d ACT=%s MIN=%d HOUR=%d"
        % (record["number"], record["active"], record["age_min"], record["age_hour"])
    )


def send_amp_states_line():
    send_uart_line(
        "AMP_STATES "
        "0=STARTUP "
        '1="WARMING FILAMENTS" '
        '2="STABILIZING B+ SUPPLY" '
        "3=OPERATE "
        "4=STANDBY "
        "5=TUBETIMER "
        "6=BALANCE "
        "7=TT_DISPLAY "
        "8=BRIGHTNESS"
    )


async def persist_state_task():
    global persist_dirty, persist_due_ms
    while True:
        if persist_dirty and time.ticks_diff(time.ticks_ms(), persist_due_ms) >= 0:
            state = {
                "volume": vol.get_current_volume(),
                "balance": vol.get_current_balance(),
                "select": sel.get_current_select(),
                "brightness": dis.get_brightness(),
            }
            try:
                with open(STATE_FILE, "w") as f:
                    json.dump(state, f)
                persist_dirty = False
                print("Persisted state:", state)
            except OSError as exc:
                print("Error writing state file:", exc)
        await uasyncio.sleep_ms(250)


async def seconds_beat():
    while True:
        await q.put(SECOND_BEAT)
        await uasyncio.sleep_ms(1000)


async def minutes_beat():
    while True:
        await q.put(MINUTE_BEAT)
        await uasyncio.sleep(60)


async def l_pb_input():
    btn_current = volpb_in.value()
    btn_last = btn_current
    while True:
        btn_current = volpb_in.value()
        if btn_current == PB_PUSHED and btn_last == PB_RELEASED:
            await q.put(L_PB_PUSHED)
        btn_last = btn_current
        await uasyncio.sleep(0.05)


async def r_pb_input():
    btn_current = selpb_in.value()
    btn_last = btn_current
    while True:
        btn_current = selpb_in.value()
        if btn_current == PB_PUSHED and btn_last == PB_RELEASED:
            await q.put(R_PB_PUSHED)
        btn_last = btn_current
        await uasyncio.sleep(0.08)


async def vol_rotated():
    while True:
        knob_current = vol_enc.change()
        if knob_current == 1:
            await q.put(VOL_KNOB_CW)
        elif knob_current == -1:
            await q.put(VOL_KNOB_CCW)
        await uasyncio.sleep(0.01)


async def sel_rotated():
    while True:
        knob_current = sel_enc.change()
        if knob_current == 1:
            await q.put(SEL_KNOB_CW)
        elif knob_current == -1:
            await q.put(SEL_KNOB_CCW)
        await uasyncio.sleep(0.01)


async def operate_input():
    operate_current = operate_in.value()
    operate_last = operate_current
    while True:
        operate_current = operate_in.value()
        if operate_current == OPERATE_ON and operate_last == OPERATE_OFF:
            await q.put(SW_OPERATE_ON)
        elif operate_current == OPERATE_OFF and operate_last == OPERATE_ON:
            await q.put(SW_OPERATE_OFF)
        operate_last = operate_current
        await uasyncio.sleep(0.10)


async def mute_input():
    mute_current = mute_in.value()
    mute_last = mute_current
    while True:
        mute_current = mute_in.value()
        if mute_current == MUTE_ON and mute_last == MUTE_OFF:
            await q.put(SW_MUTE_ON)
        elif mute_current == MUTE_OFF and mute_last == MUTE_ON:
            await q.put(SW_MUTE_OFF)
        mute_last = mute_current
        await uasyncio.sleep(0.10)


async def uart_input():
    while True:
        if uart0.any():
            raw = uart0.readline()
            if raw:
                try:
                    if isinstance(raw, str):
                        line = raw.strip()
                    else:
                        line = bytes(raw).decode("utf-8").strip()
                except UnicodeError:
                    send_uart_line("ERR BAD_VALUE")
                    line = ""
                if line:
                    await handle_uart_line(line)
        await uasyncio.sleep_ms(10)


async def handle_uart_line(line):
    parts = line.strip().split()
    if not parts:
        return

    if len(parts) == 2 and parts[0] == "GET" and parts[1] == "STATE":
        send_state_line()
        return

    if len(parts) == 2 and parts[0] == "GET" and parts[1] == "SELECTOR_LABELS":
        send_uart_line(sel.get_labels_line())
        return

    if len(parts) == 2 and parts[0] == "GET" and parts[1] == "TUBES":
        for record in tim.get_all_tube_records():
            send_tube_line(record)
        send_uart_line("TUBES_END")
        return

    if len(parts) == 2 and parts[0] == "GET" and parts[1] == "AMP_STATES":
        send_amp_states_line()
        return

    if len(parts) == 3 and parts[0] == "GET" and parts[1] == "TUBE":
        try:
            tube_num = int(parts[2])
        except ValueError:
            send_uart_line("ERR BAD_VALUE")
            return
        record = tim.get_tube_record(tube_num)
        if record is None:
            send_uart_line("ERR BAD_VALUE")
            return
        send_tube_line(record)
        return

    if len(parts) >= 3 and parts[0] == "SET":
        key = parts[1]
        value = parts[2]
        try:
            number = int(value)
        except ValueError:
            send_uart_line("ERR BAD_VALUE")
            return

        changed = False

        if key in ("VOL", "BAL", "INP", "MUTE", "BRI") and st.state in (
            STATE_BALANCE,
            STATE_BRIGHTNESS,
            STATE_TT_DISPLAY,
        ):
            st.goto_operate(vol, sel, mut, dis, tmp)

        if key == "VOL":
            changed = vol.set_volume(number)
        elif key == "BAL":
            changed = vol.set_balance(number)
        elif key == "INP":
            changed = sel.apply_select(number)
        elif key == "MUTE":
            if number not in (0, 1):
                send_uart_line("ERR BAD_VALUE")
                return
            changed = mut.set_mute_from_uart(number == 1)
        elif key == "BRI":
            old_bri = dis.get_brightness()
            dis.set_brightness(number)
            changed = dis.get_brightness() != old_bri
        elif key == "STBY":
            if number not in (0, 1):
                send_uart_line("ERR BAD_VALUE")
                return
            if number == 1 and st.state != STATE_STANDBY:
                st.goto_standby(mut, rel, dis)
                changed = True
            elif number == 0 and st.state == STATE_STANDBY:
                st.goto_filament(dis, rel)
                changed = True
        else:
            send_uart_line("ERR UNKNOWN_CMD")
            return

        if changed:
            mark_persist_dirty()
        send_uart_line("ACK")
        send_state_line()
        return

    send_uart_line("ERR UNKNOWN_CMD")


async def amp_body():
    global last_temp_published
    apply_persisted_state(load_persisted_state())
    last_temp_published = getattr(tmp, "temperature", None)

    uasyncio.create_task(l_pb_input())
    uasyncio.create_task(r_pb_input())
    uasyncio.create_task(vol_rotated())
    uasyncio.create_task(sel_rotated())
    uasyncio.create_task(operate_input())
    uasyncio.create_task(mute_input())
    uasyncio.create_task(uart_input())
    uasyncio.create_task(seconds_beat())
    uasyncio.create_task(minutes_beat())
    uasyncio.create_task(persist_state_task())

    dis.display_splash()

    while True:
        if not q.empty():
            message = await q.get()
            st.dispatch(message, vol, sel, mut, dis, rel, op, tmp, tim)
            if message == SECOND_BEAT:
                current_temp = getattr(tmp, "temperature", None)
                if current_temp != last_temp_published:
                    send_state_line()
                    last_temp_published = current_temp
            if message in (
                VOL_KNOB_CW,
                VOL_KNOB_CCW,
                SEL_KNOB_CW,
                SEL_KNOB_CCW,
                L_PB_PUSHED,
                R_PB_PUSHED,
            ):
                mark_persist_dirty()
                send_state_line()
            elif message in (SW_OPERATE_ON, SW_OPERATE_OFF, SW_MUTE_ON, SW_MUTE_OFF):
                send_state_line()
        await uasyncio.sleep_ms(10)


uasyncio.run(amp_body())
