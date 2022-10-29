from machine import Pin, I2C, Timer
import os
import time
import uasyncio
import queue


PB_PUSHED = 0        # pushbutton depressed
PB_RELEASED = 1      # pushbutton released

led_red = Pin(25, Pin.OUT)
volpb_in = Pin(7, Pin.IN, Pin.PULL_UP)
selpb_in = Pin(4, Pin.IN, Pin.PULL_UP)

#declare the queue to use for message passing
q = queue.Queue()


# Coroutine detect button press and put a value on the queue
async def l_pb_input():

    btn_current = volpb_in.value()
    btn_last = btn_current
    i=0
    while True:
        i += 1
        btn_current = volpb_in.value()
        if (btn_current == PB_PUSHED) and (btn_last == PB_RELEASED):
            await q.put(i)
        btn_last = btn_current
        await uasyncio.sleep(0.04)
    return
        

async def r_pb_input():

    btn_current = selpb_in.value()
    btn_last = btn_current
    i=0
    while True:
        i += 1
        btn_current = selpb_in.value()
        if (btn_current == PB_PUSHED) and (btn_last == PB_RELEASED):
            await q.put(i)
        btn_last = btn_current
        await uasyncio.sleep(0.1)
    return


async def main():



    #create coroutines to detect button pushes and immediately return
    uasyncio.create_task(l_pb_input())
    uasyncio.create_task(r_pb_input())

        
    while True:
        if not q.empty():
            message = await q.get()
            print("message from queue: ", message)
        await uasyncio.sleep_ms(10)
    
    return


uasyncio.run(main())