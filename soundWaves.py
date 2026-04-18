from PIL import Image
import numpy as np
import math
from MathPlus import *

def saveImage(fileName,pixels:list):
    array = np.array(pixels,dtype=np.uint8)

    newImage = Image.fromarray(array)
    newImage.save(fileName)

twoPi = 2 * math.pi

class Source():
    def __init__(self,position,wavelength=None,frequency=None,speed=None,amplitude=1,startPhase=0,isVirtual=False,virtualWall = None):
        if wavelength == 0 or frequency == 0:
            raise ValueError("wavelength and frequency must be non-zero")
        
        self.position = position
        self.amplitude = amplitude
        self.startPhase = startPhase
        
        
        if wavelength is None: wavelength = speed/frequency
        elif frequency is None: frequency = speed/wavelength
        elif speed is None: speed = frequency*wavelength
        
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
    def __init__(self,p1:Vector2D,p2:Vector2D,isAbsorber=False):
        self.start = p1
        self.end = p2
        self.vector = p2-p1
        self.unitNormal = self.vector.normal().unitVector()
        self.gradient = self.vector.gradient()
        self.isAbsorber = isAbsorber

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
        
        if abs(d) < 1e-9: return False
        
        t = crossProduct(r,v2) / d
        u = crossProduct(r,self.vector) / d
        
        if isBetween(t,0,1) and isBetween(u,0,1): return True
        else: return False
    
    
    def distanceToPoint(self,point:Vector2D):
        nearestPoint = (self.start)- self.vector*(dotProduct(self.start-point,self.vector))/(dotProduct(self.vector,self.vector))
        if isBetween(nearestPoint.x,self.start.x,self.end.x) and isBetween(nearestPoint.y,self.start.y,self.end.y):
            return (nearestPoint-point).mod()
        else:
            return math.inf

def rms(iterable):
    return math.sqrt(sum([strength**2 for strength in iterable])/len(iterable))

def calculateSounds(
    fileName,
    sources:list[Source],
    walls:list[Wall],
    maxMirrorSources=10,
    width:float|int=10,
    center:Vector2D=Vector2D(0,0),
    resolution:int=256,
    duration:float=5,
    numFrames:int=10,
    showSources:int=1,
):
    if showSources >= 1:
        sourceSize = width/100
    else:
        sourceSize = 0
    
    frameDuration = duration/numFrames
    
    increment = width / resolution
    initX , initY = center.x-width/2 , center.y-width/2
    
    sourcesAndVirtual = sources.copy()
    
    mirrorWalls = [wall for wall in walls if not wall.isAbsorber]
    
    i = 1
    for source in sourcesAndVirtual:
        i += 1
        virtualSources = []
        for wall in mirrorWalls:
            if source.vWall != wall:
                reflectionSource = wall.reflectSourceAcross(source)
                if reflectionSource != None :
                    virtualSources.append(reflectionSource)
        sourcesAndVirtual.extend(virtualSources)
        if i >= maxMirrorSources: break
    
    maxAmplitude = 0
    for source in sourcesAndVirtual:
        maxAmplitude += source.amplitude
    
    invMaxAmplitude = 255/(maxAmplitude)
    
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
                    if sourceDistance < sourceSize:
                        if showSources >= 1 and not source.isVirtual:
                            pixelDistances = "S"
                            break
                        elif showSources >= 2 and source.isVirtual:
                            pixelDistances = "V"
                            break
                    #     (If source is real    and isn't blocked by a wall ...                                                   ) or (source is virtual and is point is beyond it's mirror wall                        and isn't blocked by any other walls                                                                                )
                    elif ((not source.isVirtual and not any(wall.crossesBetweenPoints(position,source.position) for wall in walls)) or (source.isVirtual and source.vWall.crossesBetweenPoints(position,source.position) and not any(wall.crossesBetweenPoints(position,source.position) for wall in [x for x in walls if x != source.vWall]))):
                        pixelDistances.append([source,sourceDistance])
                
            pixelInfos.append(pixelDistances)
    
    print(f"Calculating Pixel Strengths")
    
    pixelStrengths = []
    for pixelInfo in pixelInfos:        
        if isinstance(pixelInfo,str):
            pixelStrengths.append(pixelInfo)
        else:
            thisPixelStrengths = []
            for frameNumber in range(numFrames):
                frameStrength = 0
                frameTime = (frameNumber*frameDuration)
                for possibleSource in pixelInfo:
                    source = possibleSource[0]
                    sourceDistance = possibleSource[1]
                    
                    phase = (sourceDistance * source.invWavelength) % 1
                    frameStrength -= math.sin( twoPi * (source.startPhase + phase - frameTime*source.frequency)) * source.amplitude
                thisPixelStrengths.append(frameStrength)
            pixelStrengths.append(rms(thisPixelStrengths))
    
    print(f"Calculating Video Pixel Colours")

    amplitudesFrame = []
    for amplitude in pixelStrengths:
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
    
    saveImage(f"{fileName}.png",convertListToFrame(amplitudesFrame))

    print("All Done")