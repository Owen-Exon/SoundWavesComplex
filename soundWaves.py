from PIL import Image
import numpy as np
import math
import imageio.v2 as imageio


def distanceSq(p1:tuple,p2:tuple):
    dX = p2[0] - p1[0]
    dY = p2[1] - p1[1]
    return dX*dX + dY*dY


def saveImage(fileName,pixels:list):
    array = np.array(pixels,dtype=np.uint8)

    newImage = Image.fromarray(array)
    newImage.save(fileName)

def saveVideo(fileName,frames,frameRate):
    frames = [np.array(img,dtype=np.uint8) for img in frames]

    if fileName[-3:] == "gif":
        imageio.mimsave(fileName, frames, fps=frameRate,loop=0)
    else:
        imageio.mimsave(fileName, frames, fps=frameRate)

twoPi = 2 * math.pi

class Source():
    def __init__(self,position,wavelength=None,frequency=None,speed=None,amplitude=1,startTime=0,startPhase=0):
        self.position = position
        self.amplitude = amplitude
        self.startTime = startTime
        self.startPhase = startPhase
        
        if wavelength == None: wavelength = speed/frequency
        elif frequency == None: frequency = speed/wavelength
        elif speed == None: speed = frequency*wavelength
        
        self.wavelength = wavelength
        self.invWavelength = 1/wavelength
        self.frequency = frequency
        self.timePeriod = 1/frequency
        self.speed = speed



def calculateSounds(sources:list[Source] = [Source(position=(0,0),wavelength=1,speed=1)],width:float|int=10,resolution:int=256,duration:float=5,framerate:int=10,timeConstant:float=1,showSources:bool=True):
    videoFrames = []

    frameTime = 1/framerate * timeConstant
    numFrames = math.ceil(duration/frameTime)
    maxAmplitude = 0
    
    center = (0,0)
    increment = width / resolution
    initX , initY = center[0]-width/2 , center[1]+width/2
    
    for source in sources:
        maxAmplitude += source.amplitude
    
    invMaxAmplitude = 255/(2*maxAmplitude)
    
    for frameNumber in range(numFrames):
        tempFrame = []
        x , y = initX , initY
        time = (frameNumber*frameTime)
        while (initY-y) < width:
            tempRow = []
            while (x-initX) < width:
                isSource = False
                strength = 0
                for source in sources:
                    pointDistanceSq = distanceSq((x,y),source.position)
                    if pointDistanceSq < 0.01 and showSources:
                        isSource = True
                        break
                    else:
                        pointDistance = math.sqrt(pointDistanceSq)
                        timeSinceSourceStart = time - source.startTime
                        if timeSinceSourceStart > pointDistance / source.speed:
                            phase = (pointDistance * source.invWavelength) % 1
                            strength -= math.sin( twoPi * (source.startPhase + phase - timeSinceSourceStart*source.frequency)) * source.amplitude
                
                if isSource:
                    tempRow.append((255,0,0)) 
                else:
                    pixelStr = int(strength*invMaxAmplitude + 127.5)
                    tempRow.append((pixelStr,pixelStr,pixelStr))           
        
                x += increment
            
            tempFrame.append(tempRow)
            x = initX
            y -= increment
            
        videoFrames.append(tempFrame)
        print(f"Frame {frameNumber} Done")
    
    saveVideo("Sound.mp4",videoFrames,framerate)
    
    print("All Done")
