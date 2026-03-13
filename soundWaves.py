from PIL import Image
import numpy as np
import math
import imageio.v2 as imageio
from MathPlus import *

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
    def __init__(self,position,wavelength=None,frequency=None,speed=None,amplitude=1,startTime=0,startPhase=0,isVirtual=False,virtualWall = None):
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
        self.isVirtual = isVirtual
        self.vWall = virtualWall
    
    def copy(self):
        tempS = Source(
            self.position,
            self.wavelength,
            self.frequency,
            self.speed,
            self.amplitude,
            self.startTime,
            self.startPhase,
            self.isVirtual,
            self.vWall
        )
        return tempS
    
def convertListToFrame(pixelGrid):
    step_size = int(math.sqrt(len(pixelGrid))) # Assumes Square
    steps = range(0, len(pixelGrid), step_size)
    grid = [pixelGrid[step:step + step_size] for step in steps]
    return list(zip(*grid))[::-1]

class Wall():
    def __init__(self,p1:Vector2D,p2:Vector2D):
        self.start = p1
        self.end = p2
        self.vector = p2-p1
        self.unitNormal = self.vector.normal().unitVector()
        self.gradient = self.vector.gradient()

    def reflectSourceAcross(self,source:Source):
        tempSource = source.copy()
        point = tempSource.position
        potentialPoint = point - 2 * (dotProduct((point-self.start),self.unitNormal)) * self.unitNormal
        
        tempSource.position = potentialPoint
        tempSource.isVirtual = True
        tempSource.vWall = self
        return tempSource 
    
    def crossesBetweenPoints(self,p1:Vector2D,p2:Vector2D):        
        v2 = p1-p2
        r = p2 - self.start
        d = crossProduct(self.vector,v2)
        
        if d == 0: return False
        
        t = crossProduct(r,v2) / d
        u = crossProduct(r,self.vector) / d
        
        if isBetween(t,0,1) and isBetween(u,0,1): return True
        else: return False
    
    
    def distanceToPoint(self,point:Vector2D):
        nearestPoint = (self.start)- self.vector*(dotProduct(self.start-point,self.vector))/(dotProduct(self.vector,self.vector))
        if isBetween(nearestPoint.x,self.start.x,self.end.x):
            return (nearestPoint-point).mod()
        else:
            return math.inf

def calculateSounds(sources:list[Source] = [Source(position=Vector2D(0,0),wavelength=1,speed=1)],walls:list[Wall]=[],width:float|int=10,resolution:int=256,duration:float=5,framerate:int=10,timeConstant:float=1,showSources:int=1,calculateAmplitude=False):

    if showSources >= 1:
        sourceSize = width/100

    if calculateAmplitude:
        for source in sources:
            source.startTime=-999
    
    frameDuration = 1/framerate * timeConstant
    numFrames = math.ceil(duration/frameDuration)
    
    increment = width / resolution
    center = Vector2D(0,0)
    initX , initY = center.x-width/2 , center.y-width/2
    
    sourcesAndVirtual = sources.copy()
    
    done = False
    for wall in walls:
        sourcesAndVirtual = sourcesAndVirtual.copy()
        virtualSources = []
        for source in sourcesAndVirtual:
            reflectionSource = wall.reflectSourceAcross(source)
            if reflectionSource != None :
                virtualSources.append(reflectionSource)
        sourcesAndVirtual.extend(virtualSources)
    
    maxAmplitude = 0
    for source in sourcesAndVirtual:
        maxAmplitude += source.amplitude
    
    invMaxAmplitude = 255/(maxAmplitude)
    halfInvMaxAmplitude = invMaxAmplitude/2
    
    print(f"Calculating Pixel Distances")
    
    pixelInfos = []
    for xIncrements in range(resolution):
        for yIncrements in range(resolution):
            position = Vector2D(initX + (increment * xIncrements) , initY + (increment * yIncrements))
            if any(wall.distanceToPoint(position) < sourceSize/4 for wall in walls):
                pixelDistances = "W"
            else: 
                pixelDistances = []
                for source in sourcesAndVirtual:
                    sourceDistance = distanceBetween2Vector2D(position,source.position)
                    if (not source.isVirtual and not any(wall.crossesBetweenPoints(position,source.position) for wall in walls) or (source.isVirtual and source.vWall.crossesBetweenPoints(position,source.position) and not any(wall.crossesBetweenPoints(position,source.position) for wall in [x for x in walls if x != source.vWall]))) or sourceDistance <= sourceSize:
                        pixelDistances.append([source,sourceDistance])
                
            pixelInfos.append(pixelDistances)
    
    print(f"Calculating Pixel Strengths")
    
    pixelStrengthFrames = []
    for frameNumber in range(numFrames):
        strengthFrame = []
        frameTime = (frameNumber*frameDuration)
        for pixelInfo in pixelInfos:
            strength = 0
            
            if pixelInfo == "W":
                strength = "W"
            else:
                for possibleSource in pixelInfo:
                    tempSource = possibleSource[0]
                    sourceDistance = possibleSource[1]
                    timeSinceSourceStart = frameTime - tempSource.startTime
                    
                    if timeSinceSourceStart >= 0 and sourceDistance < sourceSize:
                        if showSources >= 1 and not tempSource.isVirtual:
                            strength = "S"
                            break
                        elif showSources >= 2 and tempSource.isVirtual:
                            strength = "V"
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
                case "V":
                    tempFrame.append((0,255,0))
                case "W":
                    tempFrame.append((0,0,255))
                case _:
                    pixelStr = int(pixelStrength*halfInvMaxAmplitude + 127.5)
                    tempFrame.append((pixelStr,pixelStr,pixelStr)) 
        videoFrames.append(tempFrame)
    
    print(f"Saving Video")
    
    frames = [convertListToFrame(pixelGrid) for pixelGrid in videoFrames]
    [saveImage(f"outputImages/Img{i}.png",frames[i]) for i in range(len(frames))]
    saveVideo("Sound.mp4",frames,framerate)
    
    amplitudes = []
    if calculateAmplitude:
        print("Calculating Amplitude Strengths")
        
        for strengths in zip(*pixelStrengthFrames):
            if strengths[0] in ["S","V","W"]:
                amplitudes.append(strengths[0])
            else:
                amplitudes.append(math.sqrt(sum([strength**2 for strength in strengths])/len(strengths)))
                
                
        print("Calculating Amplitude Pixel Colours")
        
        amplitudesFrame = []
        for amplitude in amplitudes:
            match amplitude:
                case "S":
                    amplitudesFrame.append((255,0,0))
                case "V":
                    amplitudesFrame.append((0,255,0))
                case "W":
                    amplitudesFrame.append((0,0,255))
                case _:
                    pixelStr = int(amplitude*invMaxAmplitude)
                    amplitudesFrame.append((pixelStr,pixelStr,pixelStr))  
             
        print(f"Saving Amplitudes")     
                   
        saveImage("Amplitude.png",convertListToFrame(amplitudesFrame))
    
    print("All Done")