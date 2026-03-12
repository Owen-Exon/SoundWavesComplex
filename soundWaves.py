from PIL import Image
import numpy as np
import math
import imageio.v2 as imageio
from MathPlus import *

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

def convertListToFrame(pixelGrid):
    step_size = int(math.sqrt(len(pixelGrid))) # Assumes Square
    steps = range(0, len(pixelGrid), step_size)
    grid = [pixelGrid[step:step + step_size] for step in steps]
    return list(zip(*grid))[::-1]

def calculateSounds(sources:list[Source] = [Source(position=Vector2D(0,0),wavelength=1,speed=1)],width:float|int=10,resolution:int=256,duration:float=5,framerate:int=10,timeConstant:float=1,showSources:bool=True,calculateAmplitude=False):

    if showSources:
        sourceSize = width/100

    if calculateAmplitude:
        for source in sources:
            source.startTime=-999
    
    frameDuration = 1/framerate * timeConstant
    numFrames = math.ceil(duration/frameDuration)
    
    increment = width / resolution
    center = Vector2D(0,0)
    initX , initY = center.x-width/2 , center.y-width/2
    
    maxAmplitude = 0
    for source in sources:
        maxAmplitude += source.amplitude
    
    invMaxAmplitude = 255/(maxAmplitude)
    halfInvMaxAmplitude = invMaxAmplitude/2
    
    print(f"Calculating Pixel Distances")
    
    pixelInfos = []
    for xIncrements in range(resolution):
        for yIncrements in range(resolution):
            position = Vector2D(initX + (increment * xIncrements) , initY + (increment * yIncrements))
            pixelDistances = []
            for source in sources:
                sourceDistance = distanceBetween2Vector2D(position,source.position)
                pixelDistances.append([source,sourceDistance])
            pixelInfos.append(pixelDistances)
    
    print(f"Calculating Pixel Strengths")
    
    pixelStrengthFrames = []
    for frameNumber in range(numFrames):
        strengthFrame = []
        frameTime = (frameNumber*frameDuration)
        for pixelInfo in pixelInfos:
            strength = 0
            
            for possibleSource in pixelInfo:
                tempSource = possibleSource[0]
                sourceDistance = possibleSource[1]
                timeSinceSourceStart = frameTime - tempSource.startTime
                
                if showSources and timeSinceSourceStart >= 0 and sourceDistance < sourceSize:
                    strength = "S"
                    break
                
                if timeSinceSourceStart > sourceDistance / tempSource.speed:
                    phase = (sourceDistance * source.invWavelength) % 1
                    strength -= math.sin( twoPi * (source.startPhase + phase - timeSinceSourceStart*source.frequency)) * source.amplitude
            strengthFrame.append(strength)
        pixelStrengthFrames.append(strengthFrame)
            

        print(f"Frame {frameNumber} Done")
    
    print(f"Calculating Video Pixel Colours")
    
    videoFrames = []

    for frame in pixelStrengthFrames:
        tempFrame = []
        for pixelStrength in frame:
            match pixelStrength:
                case "S":
                    tempFrame.append((255,0,0))
                case _:
                    pixelStr = int(pixelStrength*halfInvMaxAmplitude + 127.5)
                    tempFrame.append((pixelStr,pixelStr,pixelStr)) 
        videoFrames.append(tempFrame)
    
    print(f"Saving Video")
    
    saveVideo("Sound.mp4",[convertListToFrame(pixelGrid) for pixelGrid in videoFrames],framerate)
    
    amplitudes = []
    if calculateAmplitude:
        print("Calculating Amplitude Strengths")
        
        for strengths in zip(*pixelStrengthFrames):
            if strengths[0] == "S":
                amplitudes.append("S")
            else:
                amplitudes.append(math.sqrt(sum([strength**2 for strength in strengths])/len(strengths)))
                
                
        print("Calculating Amplitude Pixel Colours")
        
        amplitudesFrame = []
        for amplitude in amplitudes:
            if amplitude == "S":
                amplitudesFrame.append((255,0,0))
            else:
                pixelStr = int(amplitude*invMaxAmplitude)
                amplitudesFrame.append((pixelStr,pixelStr,pixelStr))  
             
        print(f"Saving Amplitudes")     
                   
        saveImage("Amplitude.png",convertListToFrame(amplitudesFrame))
    
    print("All Done")
