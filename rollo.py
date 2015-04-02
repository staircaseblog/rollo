from __future__ import print_function
import pifacedigitalio
from Subfact_ina219 import INA219
import time
from optparse import OptionParser

ina = INA219()
pfd = pifacedigitalio.PiFaceDigital()
R = []

def hoch(event):
    print ("auf")
    for r in R:
        r.up()
    alle_aus()

def runter(event):
    print ("ab")
    for r in R:
        r.down()
    alle_aus()

def mitte(event):
    print ("mitte")
    for r in R:
        r.half()
    alle_aus()

def stop(event):
    print ("stop")
    alle_aus()


def alle_aus():
    for i in range(0,7):
        pfd.leds[i].value = 0
    return 0

def auf():
    alle_aus()
    pfd.leds[0].value = 0
    pfd.leds[1].value = 1    

def ab():
    alle_aus()
    pfd.leds[0].value = 1
    pfd.leds[1].value = 0

def rollo(richtung, rollo, dauer, tag):
    print("rollo: " + str(rollo) + "tag: " + tag + " richtung: " + richtung + " dauer: " + str(dauer) + "(s)")
    durchschnitt = 700
    dauer = abs(dauer)
    abschaltzeit = dauer
    startphase = True

    if rollo in range(2,7):
        # set the polarity
        if richtung == "ab":
            ab()
        else:
            auf()

        if(dauer < 180.):
            zeit = time.time()
            endezeit = zeit + dauer
            startzeit = zeit

            pfd.leds[rollo].value = 1
            current = 0

            with open("current.txt", "a") as current_log:
                ausgabe_string= "rollo: %d tag: %s richtung: %s dauer: %d (s)\n" % (rollo, tag, richtung, dauer)
                #current_log.write("rollo: " + str(rollo) + "tag:" + tag + "richtung: " + richtung + " " + str(dauer) + "s\n")
                current_log.write(ausgabe_string)

                while(endezeit > zeit and current < 1200):
                    zeit = time.time()

                    if(startphase and current > 200):
                        endezeit = zeit + dauer # set time again and start counting when current starts, thus we reduce error on incremental travels
                        startphase = False

                    current = ina.getCurrent_mA()
                    laufzeit = zeit - startzeit

                    ausgabe_string = "t: %.2f curr: %d\n" % (laufzeit, current)   
                    #current_log.write("t: " + str(laufzeit) + "current(mA): " + str(current)+ "\n")
                    current_log.write(ausgabe_string)
                    
                    if( current < 50 and laufzeit > 2):
                        abschaltzeit = max((laufzeit - 6.5), 0.0)
                        print("     cutoff: " + str(rollo) + " direction: " + richtung + " after time: " + str(abschaltzeit))
                        break

                    if( laufzeit > 1):
                        durchschnitt = (3*durchschnitt +  2*current) / 5.

                    time.sleep(0.25)

        alle_aus()

    return abschaltzeit


class Rollo:
    def __init__(self, rollo):
        self.rollo = rollo;
        self.t_ab = 0.0; # time for closing
        self.t_auf = 0.0; # time for opening
        self.position = 0 # 0 is open, 100 is closed
        self.calibrated = False
    def set_t_ab(self,t):
        self.t_ab = t
    def set_t_auf(self,t):
        self.t_auf = t
    def where_is_it(self):
        return self.position

    def calibrate(self):
        print("calibrate " + str(self.rollo))
        rollo("auf", self.rollo, 90, "ref_pos_auf")
        self.t_ab = rollo("ab", self.rollo, 90, "cal_ab")
        print(" t_ab: " + str(self.t_ab))
        self.t_auf = rollo("auf", self.rollo, 90, "cal_auf")
        print(" t_auf: " + str(self.t_auf)) 

        if(self.t_ab > self.t_auf):
            self.t_ab = self.t_auf

        self.position = 0
        self.calibrated = True
        return 1

    def go_percentage(self,p):
        if(not self.calibrated):
            self.calibrate()

        if(p < 0):
            p = 0
        if(p > 100):
            p = 100

        difference = 0.0 + p - self.where_is_it()
        direction = "auf"
        time_to_go = 0.0

        print(" position guess: " + str(self.where_is_it()) + " position to: " + str(p))

        if(difference > 0): # p > current position means down
            direction = "ab"
            time_to_go = (self.t_ab * difference)/100.
        else:
            direction = "auf"
            time_to_go = (self.t_auf * difference) /100.        

        time_to_go = abs(time_to_go)

        if(time_to_go > 2.):
            tag_string = str(self.position) + "->" + str(p)
            tt = rollo(direction, self.rollo, time_to_go, tag_string)
            self.position = p        

    def up(self):
        self.go_percentage(0)
        self.position = 0
    def down(self):
        self.go_percentage(100)
        self.position = 100
    def half(self):
        self.go_percentage(50)
        

parser = OptionParser()
parser.add_option("-r", "--richtung", dest="richtung", help="auf oder ab")

(options, args) = parser.parse_args()

listener = pifacedigitalio.InputEventListener(chip=pfd)
listener.register(0, pifacedigitalio.IODIR_ON, hoch)
listener.register(1, pifacedigitalio.IODIR_ON, runter)
listener.register(2, pifacedigitalio.IODIR_ON, mitte)
listener.register(3, pifacedigitalio.IODIR_ON, stop)
listener.activate()

if __name__ == "__main__":

    alle_aus()

    r2 = Rollo(2)
    r3 = Rollo(3) 

    R.append(r2)
    R.append(r3)

    #r2.calibrate()

    #time.sleep(10)

    #r2.half()

    #time.sleep(10)

    #r2.down()

#    if options.richtung == "ab":
#    else: # auf

    #alle_aus()

    while(True):
        time.sleep(10)
