from machine import Pin, I2C, SPI
import json
import time
import uasyncio

from config import *
from modules.display import Display
from modules.encoder import Encoder_25LB22_Q
from modules.muses72320 import Muses72320
from modules.mute import Mute
from modules.operate import Operate
from modules.relay import Relay
from modules.selector import Selector
from modules.state import State
from modules.temperature import MPC9808
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
tmp = MPC9808(i2c, dis)
tim = TubeTimer(dis)
st = State()
q = Queue(32)
persist_dirty = False
persist_due_ms = 0

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
    sel.set_select(saved.get("select", SELECT_STREAMING))
    dis.set_brightness(saved.get("brightness", INITIAL_BRIGHTNESS))


def mark_persist_dirty():
    global persist_dirty, persist_due_ms
    persist_dirty = True
    persist_due_ms = time.ticks_add(time.ticks_ms(), STATE_WRITE_DELAY_MS)


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


async def amp_body():
    apply_persisted_state(load_persisted_state())

    uasyncio.create_task(l_pb_input())
    uasyncio.create_task(r_pb_input())
    uasyncio.create_task(vol_rotated())
    uasyncio.create_task(sel_rotated())
    uasyncio.create_task(operate_input())
    uasyncio.create_task(mute_input())
    uasyncio.create_task(seconds_beat())
    uasyncio.create_task(minutes_beat())
    uasyncio.create_task(persist_state_task())

    dis.display_splash()

    while True:
        if not q.empty():
            message = await q.get()
            st.dispatch(message, vol, sel, mut, dis, rel, op, tmp, tim)
            if message in (
                VOL_KNOB_CW,
                VOL_KNOB_CCW,
                SEL_KNOB_CW,
                SEL_KNOB_CCW,
                L_PB_PUSHED,
                R_PB_PUSHED,
            ):
                mark_persist_dirty()
        await uasyncio.sleep_ms(10)


uasyncio.run(amp_body())
