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

def create2DArray(x, y, val=0):
    return [[val for i in range(y)] for j in range(x)]

def calculateSounds(sources:list[Source] = [Source(position=(0,0),wavelength=1,speed=1)],width:float|int=10,resolution:int=256,duration:float=5,framerate:int=10,timeConstant:float=1,showSources:bool=True):
    tempFrames = []

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
                    tempRow.append("S") 
                else:
                    tempRow.append(strength)           
        
                x += increment
            
            tempFrame.append(tempRow)
            x = initX
            y -= increment
            
        tempFrames.append(tempFrame)
        print(f"Frame {frameNumber} Done")
    
    size = len(tempFrames[0])
    
    amplitudesFrames = create2DArray(size,size,0)
    videoFrames = []
    
    print("Calculating Pixel Strengths")
    
    for frame in tempFrames:
        y=0
        tempFrame = create2DArray(size,size,0)
        for row in frame:
            x=0
            for strength in row:
                if strength == "S":
                    tempFrame[x][y] = (255,0,0) 
                    amplitudesFrames[x][y] = "S"
                else:    
                    pixelStr = int(strength*invMaxAmplitude + 127.5)
                    tempFrame[x][y] = (pixelStr,pixelStr,pixelStr)   
                    amplitudesFrames[x][y] += strength**2
                x+=1
            y+=1
    
    amplitudes = create2DArray(size,size,0)
    print("Calculating Amplitude Strengths")

    y=0
    for row in amplitudesFrames:
        x=0
        for strengthList in row:
            if strengthList == "S":
                amplitudes[x][y] = (255,0,0)
            else:
                strength = math.sqrt(strengthList/numFrames)
                pixelStr = int(strength*invMaxAmplitude*2)
                amplitudes[x][y] = (pixelStr,pixelStr,pixelStr)  
            x+=1
        y+=1
                    
    saveImage("Amplitude.png",amplitudes)
    
    saveVideo("Sound.mp4",videoFrames,framerate)
    
    print("All Done")
