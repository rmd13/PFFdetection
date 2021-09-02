# -*- coding: utf-8 -*-
"""
First Created on Fri Jun 11 13:11:15 2021
    Last edit on Aug,13, 2021
    # 1. install Fiji and python3-spyder3
    # 2. instalL OpenJDK8  https://cdn.azul.com/zulu/bin/zulu8.54.0.21-ca-fx-jdk8.0.292-win_x64.zip
        # unzip to D:\GreenSoft\zulu8.54.0.21-ca-fx-jdk8.0.292-win_x64
    # 3. install maven https://downloads.apache.org/maven/maven-3/3.8.1/binaries/apache-maven-3.8.1-bin.zip
        # unzip to D:\GreenSoft\apache-maven-3.8.1\bin
        # test by running <mvn -v>. Note JAVA_HOME is required
        # then add D:\GreenSoft\apache-maven-3.8.1\bin to windows environment 'Path'
    # 4. run 'pip install pyimagej'
    # 5.edit the section "--parameters to customize for each run--"
    # then run this script in spyder3 that embedded in python3
        # note, the first run will take time to auto-download supporting files.
    
@author: Ren Mengda
"""
##################--initialization-#####################
import imagej
ij = imagej.init("D:\GreenSoft\Fiji.app52p",headless=False)
ij.ui().showUI()
###################--imports--#######################
import scyjava as sj
import numpy as np
import ctypes
import struct
import time
IJ = sj.jimport('ij.IJ')
Roi = sj.jimport('ij.gui.Roi')
PolygonRoi = sj.jimport('ij.gui.PolygonRoi')
Polygon = sj.jimport('java.awt.Polygon')
ArrayList = sj.jimport('java.util.ArrayList')
Arrays = sj.jimport('java.util.Arrays')
ImageConverter = sj.jimport('ij.process.ImageConverter')
WindowManager = sj.jimport('ij.WindowManager')
GaussianBlur = sj.jimport('ij.plugin.filter.GaussianBlur')
RoiManager = sj.jimport('ij.plugin.frame.RoiManager')
ImagePlus = sj.jimport('ij.ImagePlus')
ImageCalculator = sj.jimport('ij.plugin.ImageCalculator')
ResultsTable = sj.jimport('ij.measure.ResultsTable')
###################--parameters to customize for each run--#######################
# path to jpg image
image_url ='D:\\Lab\\LKC\\BarbaraInternshipProject\\20210428_1529_10_SA-MAG_X20k_UnsonicatedPFFApr2021.jpg'
nFatigueMax = 10; 
    # For segment fracture at a vertex's forwarding segment, this number indicate the maximum allowed fractures on this segment.. 
    # This is to prevent the event of fractrue from entering a 'shallow deep PFF Gulf' too much.
        # The fracture event on the gate of 'shallow deep Gulf' usually make break close to one end of segment, causing many futile fractures.
    # Usually set to 5, but if the 'Gulf' are empty space istead of PFF, can increase to 50 or more.
aMaxSegLen = 17;
    # miniature segment length in pixels for current image
nErode = 5;
    # In the late stage before making subtraction to get PFF object,  a erode process can minimize the margin crumbs that arise from the tiny gap between the trivial mini-segments and the real edge of dark cloud arounf PFF. This number defines the intensity of this erode process.
makeMovie = 1;
    # To show the process so you can record a movie
idxCol_minorEllipsoid = 10;
    # To estimate the rough number of annexted PFF filemants in a single cluster, which colume in result table is the minorminor..
###################--functions--########################
def java_ints_to_pylist(java_ints,sj):
    if False: # my older version, ok
        aLen = java_ints.length
        aVec = []
        for i in range(aLen):
            aVec.append(sj.to_python(java_ints[i]))
        return aVec
    else: # expert version
        aVec = list(java_ints)
        return aVec
    # scyjava uses jpype, so maybe this helps:
        # https://jpype.readthedocs.io/en/latest/quickguide.html#primitives
    #Can I ask why not apply the list type conversion?
        #ja = jpype.JInt[5]
        #ja[0]=1
        #ja[1]=2
        #ja[2]=3
        #print(type(ja)) # => <java class 'int[]'>
        #pa = list(ja)
        #print(pa) # => [1,2,3]
        #print(type(pa)) # => <class 'list'>
    #@rmd13 For reference the reason that JPype returns a JInt[] rather than a Python type is that conversion costs a lot time so it is our policy to always require explicit casting. After all if someone want to get one element out of a 10MByte array with obj.callMethod()[5] the we would have converted 10 MBytes of integers into list elements just to chuck them all.
        #JPype provides conversions through duck typing. That is by pretending to be a Python type (like list or dict) at the interface level, you can simply call the standard conversion routine in Python such as str, list, or dict. That make it clear the copy is being taken. JPype conversions will be "shallow" as opposed to to_python in which it is attempting a "deep" conversion of all elements in tree of objects. "deep" conversion is more problematic as you have to have every conversion defined. Should a JInt[] got to a tuple or a list or left alone? Does Instant go to str or datetime.datetime or get left as Java object? As these are arbitrary decision JPype makes no attempt to provide them. Any decision may be right in one situation and wrong in another.
        #Not that this is addressing your issue, but hopefully gives you some background on why things work the way they do.
    #@imagejan I am guessing in this case the JInt[] may be embedded in a structure which to_python was called on. As per the usual problems with deep copies this item was not converted as there was no definition of JInt[]=>list(). I suppose you could give a map argument to the to_python method so that the user could impose a specific conversion with to_python(obj, {JInt[]:list, JChar[]:str}) where a dict gives a list of type to converter pairs. But I rejected that concept from JPype for the reasons that I have stated with deep copy.

def javaArray_to_npArray(jarray):
    npArray = np.zeros(jarray.length)
    for i in range(jarray.length):# 2048*2048 image takes 4 secnods only
        npArray[i] = ctypes.c_uint8(int(jarray[i])).value
    return npArray
######--open image    
IJ.run('Close All')
jimage = ij.io().open(image_url)
#image = ij.py.from_java(jimage) #failed for local
#ij.py.show(image, cmap='gray') # skip
#open using ij core command instead.
ips = IJ.openImage(image_url)
ips.show()
#######--Process-Filter-Gauss Blur-2.0. 
    #For this step Gauss Blur-2.0
    #    Way 1: Can use the macro recorded
    #        IJ.run(imp, "Gaussian Blur...", "sigma=2");
    #    Way 2: But here I provide another elegant way
    #        that goes into deeper the ImageJ source class actually executed underlying
    #        ij.plugin.filter.GaussianBlur
    #        And call the plugin method
aGaussianBlur = GaussianBlur();
aGaussianBlur.setup("",ips)
ip = ips.getProcessor();
aGaussianBlur.blur(ip,2.0) 
ips.updateAndDraw();
######--Edit-Invert.
    #For this step Invert
        # Way 1: Can use the macro recorded
        # Way 2:  But here I use ij.plugin.filter(.java) class which was actually executed underlying
                # which further pinpoint the ip(imageprocessor)'s invert method
                    # so I directly call ip's method invert
ip.invert()
ips.updateAndDraw();
######--Imagw-Type-8bit
ic = ImageConverter(ips);
ic.convertToGray8();
ips.updateAndDraw();
######--Image-adjust-threshold
    #Otsu? MaxEntropy is better!-dark background-apply
IJ.setAutoThreshold(ips, "MaxEntropy dark");# can also hand0adjust instead of running code for finer ctrl
######--Create a mask based on threshold area shown
ips_mask = ips.duplicate();
ip_mask = ips.createThresholdMask(); # echo ip_mask then we know its a ip type, thus swap to overwrite the ips_mask which is from copy of ips
ips_mask.setProcessor(ip_mask)
ips_mask.show()
######--Alalyze-Analyze Particles.Note the setting below:
#    :Area: 2000-Infinity
#    :droplist select the "Masks"
#    :tick the "add to manager"
IJ.run(ips_mask, "Analyze Particles...", "size=2000-Infinity show=Masks clear add")
######--get handle to masked particles
particleMaskTitle = "Mask of " + str(ips_mask.getTitle())
ips_particleMask = WindowManager.getImage(particleMaskTitle);
######--convert to normal Gray color
IJ.run(ips_particleMask, "Grays", "");
######--get RoiManager
aRoiManager = RoiManager.getInstance()
aRois = aRoiManager.getROIs()
nRoiCount = aRoiManager.getCount();
IJ.run("Colors...", "foreground=white background=black selection=yellow");
######--Cycle go through all Roi
for iRoi in range(nRoiCount):
    aRoi = aRoiManager.getRoi(iRoi)
    # make a copy of ips_particleMask destined for current roi w/o contanimation at corner(still risky, better make canvar bounds black)
    ips_aRoiSacrifice = ips_particleMask.duplicate()
    # click one ROI from roiManager to activate onto current mask image:
    ips_aRoiSacrifice.setRoi(aRoi)
    # clear all outside pixels
    IJ.run(ips_aRoiSacrifice, "Clear Outside", "");
    ips_aRoiSacrifice.show()
    # crop the current roi as tiny mask? bad!
        #ips_aRoiTile = ips_particleMask_sacrifice.crop()
        #ips_aRoiTile.show()
        #?(skip) Ctrl+Shift+D: copy each ROI tile as new subImage
        #?(skip)getConvexHull()
        # rebuild tile roi? bad! the boundary white pixels sticked to bounding! rebuild a completely false roi!
            #IJ.run(ips_aRoiTile, "Create Selection", "");
            #ips_aRoiTile.setRoi(aRoi)
    # so use ips_aRoiSacrifice instead (although more black area)
    # Edit-Selection-Convex Hull, then get a convexhull as polygon
    IJ.run(ips_aRoiSacrifice, "Convex Hull", "");
    # get convexhull roi
    hRoi = ips_aRoiSacrifice.getRoi();
    hXs = np.array(java_ints_to_pylist(hRoi.getXCoordinates(),sj))
    hYs = np.array(java_ints_to_pylist(hRoi.getYCoordinates(),sj))
    aXs = np.array(java_ints_to_pylist(aRoi.getXCoordinates(),sj))
    aYs = np.array(java_ints_to_pylist(aRoi.getYCoordinates(),sj))
    Rect= hRoi.getBoundingRect()
    aBaseX = Rect.getMinX()
    aBaseY = Rect.getMinY()
    # shrink the edge of convexhull to less than aMaxSegLen
    hXs_growing = hXs.copy()
    hYs_growing = hYs.copy()
    # making a directional indicator list for every vertex in hXs_growing
    hXs_guides = np.concatenate((hXs[2::], hXs[0:2]))
    hYs_guides = np.concatenate([hYs[2::], hYs[0:2]])      
    hXYs_guidesDir = np.ones(len(hXs_guides))
    done = 0;
    aFracturedSegIdx = 0;
    nFatigue = 0;
    aSkipAss = [];
    while True:
        if done == 1:
            break
        for iSeg in range(len(hXs_growing)):
            # its not good to fracture at same site too many times
            if iSeg in aSkipAss:
                    continue
            # define edge and guide point
            aStartX = hXs_growing[iSeg]
            aStartY = hYs_growing[iSeg]
            if iSeg == len(hXs_growing)-1:
                aEndX = hXs_growing[0]
                aEndY = hYs_growing[0]
            else:
                aEndX = hXs_growing[iSeg+1]
                aEndY = hYs_growing[iSeg+1]
            aGuideX = hXs_guides[iSeg]     
            aGuideY = hYs_guides[iSeg]
            aSegLen = ((aEndX-aStartX)**2 + (aEndY-aStartY)**2)**0.5
            if aSegLen < aMaxSegLen:
                # edge is small, No need shrink
                if iSeg==len(hXs_growing)-1:
                    done = 1;
                continue
            else:
                aSegMidX = (aStartX+aEndX)/2
                aSegMidY = (aStartY+aEndY)/2
                # select candidates aXYs_ that located in guide side(qualified for measure)
                   # guide side defined by "SegmentVector x aXY-aStartXY * hXYs_guidesDir[iSeg] > 0
                aSegVec = np.array([aEndX-aStartX,aEndY-aStartY])
                aOffVecs = np.array([aXs-aStartX,aYs-aStartY]).T
                aRefVec = np.array([aGuideX-aStartX,aGuideY-aStartY])
                aRefVecProduct =   np.cross(aSegVec,aRefVec)
                aOffVecsProducts = np.cross(aSegVec,aOffVecs)
                aUnQualifiedXYbools = aRefVecProduct*aOffVecsProducts*hXYs_guidesDir[iSeg]<=0
                # measure distance from aSegMidX/Y to all points in aX/Ys_
                aDists = ((aXs-aSegMidX)**2+(aYs-aSegMidY)**2)**0.5
                # disbale the unqualified point's distance to aSegMidXY as infinite, so never to be picked.
                aDists[aUnQualifiedXYbools] = np.inf;
                # then pick the closest points to aSegMidXY, add to convexhull.(This is called the "fracture" of this segment)
                aMinHit = np.where(np.amin(aDists)==aDists)[0][0]
                # update hXYs_guides at current "aStartXY" using aEndXY as opposite ref side
                hXs_guides[iSeg] = aEndX
                hYs_guides[iSeg] = aEndY
                hXYs_guidesDir[iSeg] = -1;
                # insert hXYs_growing by inserting the closest aXY picked
                hXs_growing = np.insert(hXs_growing,iSeg+1,aXs[aMinHit])
                hYs_growing = np.insert(hYs_growing,iSeg+1,aYs[aMinHit])
                # insert hXYs_guides at "aSegMidXY" by using aStartXY as opposite ref side
                hXs_guides = np.insert(hXs_guides,iSeg+1,aStartX)
                hYs_guides = np.insert(hYs_guides,iSeg+1,aStartY)
                hXYs_guidesDir = np.insert(hXYs_guidesDir,iSeg+1,-1)
                # before break, take note of which iSeg is fractured
                if iSeg == aFracturedSegIdx:
                    nFatigue = nFatigue + 1
                    if nFatigue > nFatigueMax:
                        aSkipAss.append(iSeg) # give up this fracture, go next
                else:
                    nFatigue = 0;
                aFracturedSegIdx = iSeg;
                if makeMovie: # can record a screen movie for presentation.
                    aShrinkRoi = PolygonRoi(PolygonRoi.toFloat(hXs_growing),PolygonRoi.toFloat(hYs_growing),len(hYs_growing),Roi.POLYGON)
                    IJ.run(ips_aRoiSacrifice, "Select None", "");
                    time.sleep(0.01)
                    aShrinkRoi.setLocation(aBaseX,aBaseY)
                    ips_aRoiSacrifice.setRoi(aShrinkRoi) 
                break
    # demo-test array 
        #j = ArrayList([1, 3, 5, 7, 9])       # <java object 'java.util.ArrayList'>
        #j = ArrayList(list(hXs_growing))     # <java object 'java.util.ArrayList'>
        #jj = j.toArray()                     # <java array 'java.lang.Object[]'>
        #hXs_growing                          # numpy.ndarray
        #PolygonRoi.toFloat(hXs_growing)      # <java array 'float[]'>
        #PolygonRoi.toFloat(list(hXs_growing))# <java array 'float[]'>
        #j = ArrayList()
        #j.append(list(hXs_growing))
        #k = Arrays.asList([1, 3, 5, 7, 9])   # <java object 'java.util.Arrays.ArrayList'>
    #aShrinkPolygon = Polygon(PolygonRoi.toInt(hXs_growing),PolygonRoi.toInt(hYs_growing),len(hYs_growing))
    #aShrinkRoi = PolygonRoi(aShrinkPolygon,Roi.POLYGON)
    aShrinkRoi = PolygonRoi(PolygonRoi.toFloat(hXs_growing),PolygonRoi.toFloat(hYs_growing),len(hYs_growing),Roi.POLYGON)
    # now have a look at the shrinked roi.Does it looks good? Is there need to adjust aMaxSegLen and re-run?
    ######--generate a mask of the shrinked roi
    IJ.run(ips_aRoiSacrifice, "Select None", "");
    ips_aRoiShrink = ips_aRoiSacrifice.duplicate()
    ips_aRoiShrink.show()
    aShrinkRoi.setLocation(aBaseX,aBaseY)
    ips_aRoiShrink.setRoi(aShrinkRoi)  # Uh??? roi moved to upperleft corner! solved by upper line aBaseXY.
    ip_aRoiShrinkMask = ips_aRoiShrink.createRoiMask();
    ips_aRoiShrinkMask = ImagePlus("shrinkedOuterMask",ip_aRoiShrinkMask)
    ips_aRoiShrinkMask.show()
    ######--do a further erode of shrinked roi's mask to further miniate the tiny margins that might contaminate in the final result
    for i in range(nErode):
        IJ.run(ips_aRoiShrinkMask, "Erode", "");
    ######--remove roi from ips_aRoiSacrifice, then invert image
    IJ.run(ips_aRoiShrink, "Select None", "");
    IJ.run(ips_aRoiShrink, "Invert", "");
    ######--multiply ips_aRoiSacrifice to ips_aRoiShrink
    aImageCalculator = ImageCalculator();
    ips_PFF = aImageCalculator.run("Multiply create", ips_aRoiShrink, ips_aRoiShrinkMask)
    ips_PFF.show()
    ######--get Perimeter & Area of all PFF in this tile
    ips_PFFerode = ips_PFF.duplicate();
    IJ.run(ips_PFFerode, "Erode", "");
        #a = ips_PFF.getProcessor().getPixels()
        #b = int(a[1])
        #c = ctypes.c_uint8(-5)
        #d = c.value
    aMatrix_PFF = javaArray_to_npArray(ips_PFF.getProcessor().getPixels()) #<java array 'byte[]'>
    aMatrix_PFF2 = javaArray_to_npArray(ips_PFFerode.getProcessor().getPixels()) #<java array 'byte[]'>
    aPerimeter_PFF = (aMatrix_PFF.sum() - aMatrix_PFF2.sum())/255
    aArea_PFF = aMatrix_PFF.sum()/255
    ######--get isoLength and isoHeight for current PFF tile
    isoLen_PFF = (aPerimeter_PFF + (aPerimeter_PFF**2 - 16*aArea_PFF)**0.5)/4
    isoThick_PFF = (aPerimeter_PFF - (aPerimeter_PFF**2 - 16*aArea_PFF)**0.5)/4
    perimeter_area_ratio = aPerimeter_PFF/aArea_PFF
    # detect PFF's roi
    ic = ImageConverter(ips_PFF);
    ic.convertToGray8();
    ips_PFF.updateAndDraw();
    IJ.run(ips_PFF, "Create Selection", "");
    roi_PFF = ips_PFF.getRoi()
        # roi_PFF defines the exact contour of PFF materials on this PFF cluster on TEM images 
    # get most fitted ellipsoid major and minor length
    IJ.run("Clear Results", "");
    IJ.run(ips_PFF, "Measure", "");
    aResultsTable = ResultsTable.getResultsTable()
    aResultImg = aResultsTable.getTableAsImage()
        # should get float, but read the return 4 bytes of this float as a int32. So need cast int32 to single(32-bit float)
    aPixelValue = aResultImg.getPixel(idxCol_minorEllipsoid,0)
    singleBytes = aPixelValue.to_bytes(4,'little')
        #singleBytes = int(aResultImg.getPixel(10,0)).to_bytes(4,'little')
    aEllipsoidMinorLen = struct.unpack('<f',singleBytes)   #little endian. test Correct!
        # struct.unpack('>f', singleBytes) #big endian
        # ctypes.c_float(int(aPixelValue)) #wrong! soft conversion, not hard typecast!
    # rough estimation of how many parallel PFF filaments in this PFF cluster
    nPFF = aEllipsoidMinorLen/isoThick_PFF
    # rough estimation of mean length of individual PFF filaments in this PFF cluster
    meanLen_PFF = isoLen_PFF/nPFF2
    
