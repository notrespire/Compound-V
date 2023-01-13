from lib import BFV
from lib.bones import bones
import time
import math
from ctypes import *
from pynput.mouse import Button, Controller
from difflib import SequenceMatcher
import pydirectinput
from threading import Thread
from playsound import playsound
import os
import logging
import random

from rich.text import Text
from rich import print
from rich.layout import Layout
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich import box

console = Console()
layout = Layout()
debug = 1

bannerText = """\
      _____                                  __   _   __
     / ___/__  __ _  ___  ___  __ _____  ___/ /__| | / /
    / /__/ _ \/  ' \/ _ \/ _ \/ // / _ \/ _  /___/ |/ / 
    \___/\___/_/_/_/ .__/\___/\_,_/_//_/\_,_/    |___/  
                /_/         
        """

layout.split_column(
    Layout(name="upper", ratio=2),
    Layout(name="lower", ratio=5)
)
layout["upper"].update(
    Align.center(
        Panel.fit(bannerText, title="v1.1", subtitle="Created by survivalizeed. UI by notRespire", style="light_slate_grey", box=box.HORIZONTALS)
    )
)

# Debug Log File, if needed
logging.basicConfig(filename='compoundv.log', encoding='utf-8', level=logging.DEBUG)

class Aimer:
    tick = 0
    closestDistance = 9999
    closestSoldier = None
    closestSoldierMovementX = 0
    closestSoldierMovementY = 0
    lastSoldier = 0
    screensize = (0, 0)
    dodge = False 

    def __init__(self, collection):
        self.collection = collection
        self.fov = collection[0]
        self.distance_limit = collection[1]
        self.trigger = collection[2]
        self.autoshoot = collection[3]
        self.autoscope = collection[4]
        self.aim_locations = collection[5]
        self.aim_switch = collection[6]
        self.screensize = collection[7]
        self.huntToggle = collection[8]
        self.huntTargetSwitch = collection[9]
        self.dodgeMode = collection[10]
        self.crouch_Key = collection[11]
        self.toggle_autoshoot = collection[12]
        self.toggle_dodge_Mode = collection[13]
        self.toggle_keep_target = collection[14]
        self.random_aim_toggle = collection[15]
        
    def DebugPrintMatrix(self, mat):
        print("[%.3f %.3f %.3f %.3f ]" % (mat[0][0], mat[0][1], mat[0][2], mat[0][3]))
        print("[%.3f %.3f %.3f %.3f ]" % (mat[1][0], mat[1][1], mat[1][2], mat[1][3]))
        print("[%.3f %.3f %.3f %.3f ]" % (mat[2][0], mat[2][1], mat[2][2], mat[2][3]))
        print("[%.3f %.3f %.3f %.3f ]\n" % (mat[3][0], mat[3][1], mat[3][2], mat[3][3]))

    def DebugPrintVec4(self, Vec4):
        print("[%.3f %.3f %.3f %.3f ]\n" % (Vec4[0], Vec4[1], Vec4[2], Vec4[3]))

    def accelDistance(self, distance):
        leftMin = 0
        rightMin = 0.5
        leftSpan = 100 - 0
        rightSpan = 1.2 - 0.5

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(distance - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)

        # return 0.0 + (distance - 0) / 20 * 100

    def dodgeIt(self):
        while True:
            if self.dodge:
                pydirectinput.press(self.crouch_Key)
            time.sleep(0.01)
            
    def start(self):
        console.print(Text("[+] Searching for BFV.exe", style="blue"))

        phandle = BFV.get_handle()

        if phandle:
            console.print(Text("[!] BFV.exe found, Handle 0x%x" % phandle, style="green"))
            console.print()
            time.sleep(1)
        else:
            console.print(Text("[X] Error: Cannot find BFV.exe", style="red"))
            exit(1)

        cnt = 0
        # mouse = Controller()
        self.lastSoldier = 0
        self.lastX = 0
        self.lastY = 0
        aim_location_index = 0
        aim_location_max = len(self.aim_locations) - 1
        aim_switch_pressed = False

        aim_location_names = []
        for location in self.aim_locations:
            for key in bones:
                if bones[key] == location:
                    aim_location_names.append(key)
                    
        # Set Aim Bone to current aim location
        aimBone = self.aim_locations[aim_location_index]
        aimBoneName = aim_location_names[aim_location_index]
        
        # m = Mouse()
        pressedCounter = 0
        pressed = False
        pressedL = False
        huntMode = False
        keepTarget = False
        huntSoldier = None
        huntSoldierName = None
        random_aim_bone = False
        mouse = Controller()
    
        dodge = Thread(target=self.dodgeIt)
        dodge.start()

        def genTable() -> layout:
            table = Table(title="Options:", show_lines=True, expand=True, box=box.ROUNDED, style="bright_black")
            table.add_column("Name", justify="left", style="bright_white", ratio=3),
            table.add_column("Status", justify="center", style="bright_white", ratio=1)
            table.add_row("AutoShoot", f'{"Enabled" if self.autoshoot else "Disabled"}', style=f'{"dark_green" if self.autoshoot else "dark_red"}'),
            table.add_row("AutoScope", f'{"Enabled" if self.autoscope else "Disabled"}', style=f'{"dark_green" if self.autoscope else "dark_red"}'),
            table.add_row("AutoDodge", f'{"Enabled" if self.dodgeMode else "Disabled"}', style=f'{"dark_green" if self.dodgeMode else "dark_red"}'),
            table.add_row("KeepTarget", f'{"Enabled" if keepTarget else "Disabled"}', style=f'{"dark_green" if keepTarget else "dark_red"}'),
            table.add_row("Hunt Mode", f'{huntSoldierName if huntMode else "Disabled"}', style=f'{"dark_green" if huntMode else "dark_red"}'),
            table.add_row("FOV", f"{self.fov}", style="grey50")
            table.add_row("Distance", f"{self.distance_limit}", style="grey50")
            table.add_row("Bone", f'{"[bold dark_green]Random" if random_aim_bone else f"[bold bright_white]{aimBoneName}"}', end_section=True, style="grey50")
            
            layout["lower"].update(
                Panel(table, style="light_slate_grey", box=box.ROUNDED)
            )
            
            print(layout, end="\r", flush=True)
        
        with console.status("[!] Compound-V Loading", spinner="arc"):
            time.sleep(3)
            genTable()
        
        while 1:
                #Generate Random Aim Bone from the existing Array
                if random_aim_bone:
                    aimBone = random.choice(self.aim_locations)
                else:
                    #change aim location index if key is pressed
                    if self.aim_switch:
                        if cdll.user32.GetAsyncKeyState(self.aim_switch) & 0x8000:
                            aim_switch_pressed = True
                            random_aim_bone = False
                            aimBone = self.aim_locations[aim_location_index]
                            aimBoneName = aim_location_names[aim_location_index]
                            genTable()
                        elif aim_switch_pressed:
                            aim_switch_pressed = False
                            aim_location_index = aim_location_index + 1
                            if aim_location_index > aim_location_max:
                                aim_location_index = 0
                            aimBone = self.aim_locations[aim_location_index]
                            aimBoneName = aim_location_names[aim_location_index]
                            genTable()

                BFV.process(phandle, cnt, aimBone)
                cnt += 9999

                data = BFV.gamedata
                self.closestDistance = 9999
                self.closestSoldier = None
                self.closestSoldierMovementX = 0
                self.closestSoldierMovementY = 0
                
                if cdll.user32.GetAsyncKeyState(self.random_aim_toggle) & 0x8000:
                    random_aim_bone = not random_aim_bone
                    if random_aim_bone:
                        random_aim_bone = True
                        Thread(target=playsound, args=(os.getcwd() + '/snd/activate.mp3',), daemon=True).start()
                        genTable()
                    else:
                        random_aim_bone = False
                        Thread(target=playsound, args=(os.getcwd() + './snd/deactivate.mp3',), daemon=True).start()
                        genTable()
                    time.sleep(0.3)

                if cdll.user32.GetAsyncKeyState(self.toggle_keep_target) & 0x8000:
                    keepTarget = not keepTarget
                    if keepTarget:
                        Thread(target=playsound, args=(os.getcwd() + '/snd/activate.mp3',), daemon=True).start()
                        genTable()
                    else:
                        Thread(target=playsound, args=(os.getcwd() + './snd/deactivate.mp3',), daemon=True).start()
                        genTable()
                    time.sleep(0.3)

                if cdll.user32.GetAsyncKeyState(self.huntToggle) & 0x8000:
                    if not data.soldiers:
                        console.print(Text("[X] You are currently not in a round", style="red"))
                    elif huntSoldier is None:
                        console.print(Text("[X] No Soldier to hunt chosen"), style="red")
                    else:
                        huntMode = not huntMode
                        if huntMode:
                            self.distance_limit = None
                            Thread(target=playsound, args=(os.getcwd() + '/snd/activate.mp3',), daemon=True).start()
                            genTable()
                        else:
                            self.distance_limit = self.collection[1]
                            Thread(target=playsound, args=(os.getcwd() + './snd/deactivate.mp3',), daemon=True).start()
                            genTable()
                    time.sleep(0.3)
                
                if cdll.user32.GetAsyncKeyState(self.huntTargetSwitch) & 0x8000:
                    if not data.soldiers:
                        print(Text("[X] You are currently not in a round", style="red"))
                    else:
                        print()
                        name = console.input("[!] [bold bright_white]Enter a name to hunt:")
                        ratios = []
                        for soldier in data.soldiers:
                            ratios += [SequenceMatcher(None, name, soldier.name).ratio()]
                        huntSoldierName = data.soldiers[ratios.index(max(ratios))].name
                        genTable()
                    time.sleep(0.3)

                for soldier in data.soldiers:
                    if huntSoldierName is None:
                        break
                    if soldier.name == huntSoldierName:
                        huntSoldier = soldier
                        break

                if cdll.user32.GetAsyncKeyState(self.toggle_autoshoot) & 0x8000:
                    self.autoshoot = not self.autoshoot
                    if self.autoshoot:
                        Thread(target=playsound, args=(os.getcwd() + '/snd/activate.mp3',), daemon=True).start()
                        genTable()
                    else:
                        Thread(target=playsound, args=(os.getcwd() + '/snd/deactivate.mp3',), daemon=True).start()
                        genTable()
                    time.sleep(0.3)
                    
                if cdll.user32.GetAsyncKeyState(self.toggle_dodge_Mode) & 0x8000:
                    self.dodgeMode = not self.dodgeMode
                    if self.dodgeMode:
                        Thread(target=playsound, args=(os.getcwd() + '/snd/activate.mp3',), daemon=True).start()
                        genTable()
                    else:
                        Thread(target=playsound, args=(os.getcwd() + '/snd/deactivate.mp3',), daemon=True).start()
                        genTable()
                    time.sleep(0.3)

                if self.lastSoldier != 0:
                    if cdll.user32.GetAsyncKeyState(self.trigger) & 0x8000 or huntMode:
                        found = False
                        for Soldier in data.soldiers:
                            if huntMode and huntSoldier != Soldier: 
                                continue
                            if self.lastSoldier == Soldier.ptr:
                                found = True
                                if Soldier.occluded:
                                    if keepTarget:
                                        mouse.release(Button.left)
                                    else:
                                        self.lastSoldier = 0
                                        self.closestSoldier = None
                                        self.lastX = 0
                                        self.lastY = 0
                                        continue
                                try:
                                    dw, distance, delta_x, delta_y, Soldier.ptr, dfc = self.calcAim(data, Soldier)
                                    self.closestDistance = dfc
                                    self.closestSoldier = Soldier

                                    #accel = 0  # this is WIP
                                    self.closestSoldierMovementX = delta_x# + (self.lastX * accel)
                                    self.closestSoldierMovementY = delta_y# + (self.lastY * accel)
                                    self.lastX = delta_x
                                    self.lastY = delta_y
                                    continue
                                    # print("x: %s" % delta_x)
                                except Exception as e:
                                    self.lastSoldier = 0
                                    self.closestSoldier = None
                                    #print("Disengaging: soldier no longer meets criteria: %s" % e)
                        if not found:
                            self.lastSoldier = 0
                            self.closestSoldier = None
                            self.lastX = 0
                            self.lastY = 0
                            #print("Disengaging: soldier no longer found")
                    else:
                        self.lastSoldier = 0
                        self.closestSoldier = None
                        self.lastX = 0
                        self.lastY = 0
                        #print("Disengaging: key released")
                else:
                    distanceList = []
                    for Soldier in data.soldiers:
                        if huntMode and huntSoldier != Soldier: 
                            continue
                        try:
                            dw, distance, delta_x, delta_y, Soldier.ptr, dfc = self.calcAim(data, Soldier)
                            if dw > self.fov:
                                continue
                            
                            if Soldier.occluded:
                                continue

                            if self.distance_limit is not None and distance > self.distance_limit:
                                continue

                            distanceList += [distance]
                            if distance <= min(distanceList):
                                if dfc < self.closestDistance:  # is actually comparing dfc, not distance
                                    if cdll.user32.GetAsyncKeyState(self.trigger) & 0x8000 or huntMode:
                                        self.closestDistance = dfc
                                        self.closestSoldier = Soldier
                                        self.closestSoldierMovementX = delta_x
                                        self.closestSoldierMovementY = delta_y
                                        self.lastSoldier = Soldier.ptr
                                        self.lastSoldierObject = Soldier
                                        self.lastX = delta_x
                                        self.lastY = delta_y
                                        self.distance = distance
                        except:
                            # print("Exception", sys.exc_info()[0])
                            continue
                    status = "[%s] " % aim_location_names[aim_location_index]
                    if self.lastSoldier != 0:
                        if self.autoscope:
                            pressed = True
                            pressedCounter = 0
                            mouse.press(Button.right)
                            
                        if self.lastSoldierObject.name != "": 
                            name = self.lastSoldierObject.name
                            if self.lastSoldierObject.clan != "":
                                name = "[%s]%s" % (self.lastSoldierObject.clan, name)
                        else:
                            name = "0x%x" % self.lastSoldier
                        status = status + "locked onto %s" % name
                    else:
                        status = status + "idle"
                        pressedCounter += 1
                        if pressed and self.autoscope and pressedCounter >= 50:
                            mouse.release(Button.right)
                            pressedCounter = 0
                            pressed = False
                    if not huntMode:
                        print("[bright_black]\[status][/bright_black] [bold bright_white]Running[/bold bright_white]", flush=True, end="\r")
                        # print("%-50s" % status, end="\r")
                    if huntMode and huntSoldierName is not None:
                        print(f"[!] Current Hunt: [bold bright_white][{huntSoldier.clan}]{huntSoldier.name}[/bold bright_white], Distance: [bold bright_white]{round(self.FindDistance(huntSoldier.transform[3][0], huntSoldier.transform[3][1], huntSoldier.transform[3][2], data.mytransform[3][0], data.mytransform[3][1], data.mytransform[3][2]), 1)}[/bold]", end="\r", flush=True)
                        
                        # print("[!] Current Hunt: ", "[%s]%s" % (huntSoldier.clan, huntSoldier.name), "Distance: ", round(self.FindDistance(huntSoldier.transform[3][0], huntSoldier.transform[3][1], huntSoldier.transform[3][2],
                        #                 data.mytransform[3][0], data.mytransform[3][1], data.mytransform[3][2]), 1), end="\r", flush=True)
                if pressedL:
                    if self.autoshoot:
                        mouse.release(Button.left)
                    if self.dodgeMode:
                        self.dodge = False
                    pressedL = False
                if self.closestSoldier is not None:
                    if cdll.user32.GetAsyncKeyState(self.trigger) & 0x8000 or huntMode:
                        if self.closestSoldierMovementX > self.screensize[0] / 2 or self.closestSoldierMovementY > \
                                self.screensize[1] / 2:
                            continue
                        else:
                            if abs(self.closestSoldierMovementX) > self.screensize[0]:
                                continue
                            if abs(self.closestSoldierMovementY) > self.screensize[1]:
                                continue
                            if self.closestSoldierMovementX == 0 and self.closestSoldierMovementY == 0:
                                continue
                            self.move_mouse(int(self.closestSoldierMovementX), int(self.closestSoldierMovementY - int(self.distance * 0.03)))
                            if self.dodgeMode:
                                self.dodge = True
                            if self.autoshoot:
                                if not self.closestSoldier.occluded:  
                                    mouse.press(Button.left)
                            pressedL = True
                            time.sleep(0.001)


    def calcAim(self, data, Soldier):

        transform = Soldier.aim

        transform[0] = transform[0] + Soldier.accel[0] - data.myaccel[0]
        transform[1] = transform[1] + Soldier.accel[1] - data.myaccel[1]
        transform[2] = transform[2] + Soldier.accel[2] - data.myaccel[2]


        x, y, w = self.World2Screen(data.myviewmatrix, transform[0], transform[1], transform[2])

        distance = self.FindDistance(Soldier.transform[3][0], Soldier.transform[3][1], Soldier.transform[3][2],
                                     data.mytransform[3][0], data.mytransform[3][1], data.mytransform[3][2])

        dw = distance - w

        delta_x = (self.screensize[0] / 2 - x) * -1
        delta_y = (self.screensize[1] / 2 - y) * -1

        dfc = math.sqrt(delta_x ** 2 + delta_y ** 2)

        return dw, distance, delta_x / 2, delta_y / 2, Soldier.ptr, dfc

    def FindDistance(self, d_x, d_y, d_z, l_x, l_y, l_z):
        distance = math.sqrt((d_x - l_x) ** 2 + (d_y - l_y) ** 2 + (d_z - l_z) ** 2)
        return distance

    def World2Screen(self, MyViewMatrix, posX, posY, posZ):

        w = float(
            MyViewMatrix[0][3] * posX + MyViewMatrix[1][3] * posY + MyViewMatrix[2][3] * posZ + MyViewMatrix[3][3])

        x = float(
            MyViewMatrix[0][0] * posX + MyViewMatrix[1][0] * posY + MyViewMatrix[2][0] * posZ + MyViewMatrix[3][0])

        y = float(
            MyViewMatrix[0][1] * posX + MyViewMatrix[1][1] * posY + MyViewMatrix[2][1] * posZ + MyViewMatrix[3][1])

        mX = float(self.screensize[0] / 2)
        mY = float(self.screensize[1] / 2)

        x = float(mX + mX * x / w)
        y = float(mY - mY * y / w)

        return x, y, w

    def move_mouse(self, x, y):  # relative
        ii = Input_I()
        ii.mi = MouseInput(x, y, 0, 0x1, 0, pointer(c_ulong(0)))
        command = Input(c_ulong(0), ii)
        windll.user32.SendInput(1, pointer(command), sizeof(command))


PUL = POINTER(c_ulong)


class KeyBdInput(Structure):
    _fields_ = [("wVk", c_ushort),
                ("wScan", c_ushort),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(Structure):
    _fields_ = [("uMsg", c_ulong),
                ("wParamL", c_short),
                ("wParamH", c_ushort)]


class MouseInput(Structure):
    _fields_ = [("dx", c_long),
                ("dy", c_long),
                ("mouseData", c_ulong),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class POINT(Structure):
    _fields_ = [("x", c_long),
                ("y", c_long)]


class Input_I(Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(Structure):
    _fields_ = [("type", c_ulong),
                ("ii", Input_I)]
