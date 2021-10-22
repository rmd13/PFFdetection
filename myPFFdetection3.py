# -*- coding: utf-8 -*-
"""
@author: Ren Mengda
First Created on Fri Jun 11 13:11:15 2021
    Edit on Aug,13, 2021
    Edit on Sep,1, 2021
    Edit on Oct,5, 2021
    #1. install Fiji from https://downloads.imagej.net/fiji/latest/fiji-win64.zip
        install Python3.6.6 from https://www.python.org/ftp/python/3.6.6/python-3.6.6.exe
        install spyder3.3.1 by commands  'pip install spyder==3.3.1' into command window.
        place ij_ridge_detect-1.4.0-J6Public.jar inside Fiji's installation .\Plugins folder.
        instalL OpenJDK8  https://cdn.azul.com/zulu/bin/zulu8.54.0.21-ca-fx-jdk8.0.292-win_x64.zip
            unzip to a folder like D:\GreenSoft\zulu8.54.0.21-ca-fx-jdk8.0.292-win_x64 and add to windows environment 'Path'.
       install maven 3.8.1
            https://maven.apache.org/download.cgi
            https://downloads.apache.org/maven/maven-3/3.8.1/binaries/apache-maven-3.8.1-bin.zip
            unzip to a folder like D:\GreenSoft\apache-maven-3.8.1\bin 
            test by running <mvn -v>. Note JAVA_HOME is required
            then add D:\GreenSoft\apache-maven-3.8.1\bin to windows environment 'Path'.
        install pyimagej by commands 'pip install pyimagej' into command window.
    #2. Run imagej, click Analyze-Set Measurement..., tick as image blow shows.
    #3. launch spyder3 GUI by input 'spyder3.exe' into command window.
        it usually localized in C:\Users\~\AppData\Local\Programs\Python\Python36\Scripts\spyder3.exe
    #4. Open this script to run in spyder3.
        edit the line in this script to change to your local Fiji application path.
            FijiAppPath = "D:\GreenSoft\Fiji.app52p" # Fiji installation path
    # then run the whole script in Spyder3.
        # note, the first run will take time to auto-download supporting files.
    IJ.run('Close All')
"""
##################--initialization-#####################
# this section must run once only in the very beginning.
from tkinter import Tk, filedialog
def uigetdir(prompt):
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    open_file = filedialog.askdirectory(title=prompt)    
    rtFolder = open_file.replace('/','\\')
    return rtFolder
import os
if 'FijiAppPath' not in locals():
    FijiAppPath = "D:\GreenSoft\Fiji.app52p" # Fiji installation path
    if not os.path.isdir(FijiAppPath):
        FijiAppPath = uigetdir('Select a Fiji installation folder')
    import imagej
    ij = imagej.init(FijiAppPath,headless=False)
    ij.ui().showUI()
    import sys
    sys.exit() # then run again to process the images.
    
##################--parameters-#####################
aFmt = '.jpg' # extension of input image
GaussSigma = 2.5 #default 1.5
aThresholdMtd = "Triangle dark" #"MaxEntropy dark" # #
nFatigueMax = 50 # default30; #10 by default
    # For segment fracture at a vertex's forwarding segment, this number indicate the maximum allowed fractures on this segment.. 
    # This is to prevent the event of fractrue from entering a 'sharp deep PFF Gulf' too much.
        # The fracture event on the gate of 'shallow deep Gulf' usually make break close to one end of segment, causing many futile fractures.
    # Usually set to 5~10, but if the 'Gulf' are empty space istead of PFF, can increase to 50 or more.
nGiveupMax = 2000;
aMaxSegLen = 10;
    # miniature segment length in pixels for current image underwhich no further fracture will be considered.
nErode = 5;
    # In the late stage before making subtraction to get PFF object,  a erode process can minimize the margin crumbs that arise from the tiny gap between the trivial mini-segments and the real edge of dark cloud arounf PFF. This number defines the intensity of this erode process.
makeMovie = 0;
    # To show the process so you can record a movie
PFF_crumblePixelAreaThreshold = 20;
    # to remove tiny PFF ROI.
idxCol_minorEllipsoid = 10;
    # = 0-based index of Column "Minor" in Results table. Must pre-set default measure option and get beforahnd.
    # To estimate the rough number of annexted PFF filemants in a single cluster, which colume in result table is the minorminor.
idxCol_length = 6;
idxCol_area = 1;

inTriExtruDistMinThresh = 4;
pixel_nm = 200/240;
##################--dead parameters-#####################
aDiameterBuff = 0;
###################--imports--#######################
import scyjava as sj
import numpy as np
import ctypes
import struct
import time
import glob
import csv
from decimal import Decimal
IJ                 = sj.jimport('ij.IJ')
ImagePlus          = sj.jimport('ij.ImagePlus') 
Roi                = sj.jimport('ij.gui.Roi')
PolygonRoi         = sj.jimport('ij.gui.PolygonRoi')
Polygon            = sj.jimport('java.awt.Polygon')
ArrayList          = sj.jimport('java.util.ArrayList')
Arrays             = sj.jimport('java.util.Arrays')
ImageConverter     = sj.jimport('ij.process.ImageConverter')
WindowManager      = sj.jimport('ij.WindowManager')
GaussianBlur       = sj.jimport('ij.plugin.filter.GaussianBlur')
RoiManager         = sj.jimport('ij.plugin.frame.RoiManager')
ImagePlus          = sj.jimport('ij.ImagePlus')
ImageCalculator    = sj.jimport('ij.plugin.ImageCalculator')
ResultsTable       = sj.jimport('ij.measure.ResultsTable')
RoiEncoder         = sj.jimport('ij.io.RoiEncoder')
Lines              = sj.jimport('de.biomedical_imaging.ij.steger.Lines_')
Macro              = sj.jimport('ij.Macro')

###################--inputs--#######################
import tkinter as tk
def fetch(entries,answers,root):
    for entry in entries:
        field = entry[0]
        text  = entry[1].get()
        print('%s: "%s"' % (field, text)) 
        answers.append(text)
    root.destroy()

def makeform(root, fields,defAnss):
    entries = []
    idx = -1;
    for field in fields:
        idx = idx + 1
        row = tk.Frame(root)
        lab = tk.Label(row, width=80, text=field, anchor='w')
        ent = tk.Entry(row)
        ent.insert(-1,defAnss[idx])
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        entries.append((field, ent))
    return entries

def qurestdlg(fields,defAnss):
    answers = [];
    root = tk.Tk()
    root.title("Parameters")  
    ents = makeform(root, fields,defAnss)
    #root.bind('<Return>', (lambda event, e=ents: fetch(e,answers,root)))   
    b1 = tk.Button(root, text='OK',
                  command=(lambda e=ents: fetch(e,answers,root)))
    b1.pack(side=tk.LEFT, padx=5, pady=5)
    b2 = tk.Button(root, text='Quit', command=root.destroy)
    b2.pack(side=tk.LEFT, padx=5, pady=5)
    root.lift()
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)
    root.mainloop()
    return answers

fields = ['Image format', aFmt,\
          'Gauss Sigma factor', str(GaussSigma),\
          'Thresholding method',aThresholdMtd,\
          'Minimum length of segment(in pixel) allowed to apply shrink',str(aMaxSegLen),\
          'Number of consecutive maximum shrinks allowed on the same edge start point',str(nFatigueMax),\
          'Minimum extrusion distance(in pixel) considered to search for alternative inside halfTriangle',str(inTriExtruDistMinThresh),\
          'Maximum number of total shrinks allowed for a PFF clump',str(nGiveupMax),\
          'Number of rounds of erodes before multiply to get PFF (to remove tiny surrounding dots)',str(nErode),\
          'Show the real-time shrink process on screen? 0=OFF,1=ON (Caution: will slow the process)',str(makeMovie),\
          'Minimum pixels allowed to filter final non-PFF crumbles',str(PFF_crumblePixelAreaThreshold),\
          'The 0-based index of column Minor in results table',str(idxCol_minorEllipsoid),\
          'The 0-based index of column Length in RidgeDetection table',str(idxCol_length),\
          'Pixel length in reality (in nanometer)',str(pixel_nm)\
          ]
answers = qurestdlg(fields[0::2],fields[1::2]);print(answers)
charIdxs = [0,2];numericIdx = [1];numericIdx.extend([i for i in range(3,13)])
aFmt,aThresholdMtd =  [answers[i] for i in charIdxs]
GaussSigma,aMaxSegLen,nFatigueMax,inTriExtruDistMinThresh,\
nGiveupMax,nErode,makeMovie,PFF_crumblePixelAreaThreshold,\
idxCol_minorEllipsoid,idxCol_length,pixel_nm = [float(answers[i]) for i in numericIdx]
###################--functions--########################
def java_ints_to_pylist(java_ints,sj):
    if False: # my older version, also ok
        aLen = java_ints.length
        aVec = []
        for i in range(aLen):
            aVec.append(sj.to_python(java_ints[i]))
        return aVec
    else: # expert version, better
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

def PointInTriangle(point,tri_points):
    # tri_points =  [(1,1),(2,3),(3,1)]
    Dx , Dy = point
    A,B,C = tri_points
    Ax, Ay = A
    Bx, By = B
    Cx, Cy = C
    M1 = np.array([ [Dx - Bx, Dy - By, 0],
                    [Ax - Bx, Ay - By, 0],
                    [1      , 1      , 1]
                  ])
    M2 = np.array([ [Dx - Ax, Dy - Ay, 0],
                    [Cx - Ax, Cy - Ay, 0],
                    [1      , 1      , 1]
                  ])
    M3 = np.array([ [Dx - Cx, Dy - Cy, 0],
                    [Bx - Cx, By - Cy, 0],
                    [1      , 1      , 1]
                  ])
    M1 = np.linalg.det(M1)
    M2 = np.linalg.det(M2)
    M3 = np.linalg.det(M3)
    if(M1 == 0 or M2 == 0 or M3 ==0):
        # print("Point: ",point," lies on the arms of Triangle")
        return 0
    elif((M1 > 0 and M2 > 0 and M3 > 0)or(M1 < 0 and M2 < 0 and M3 < 0)):
        # if products is non 0 check if all of their sign is same
        # print("Point: ",point," lies inside the Triangle")
        return 1
    else:
        # print("Point: ",point," lies outside the Triangle")
        return -1

def process_one_image(image_url):
    if False:
        image_url = 'D:\\Lab\\LKC\\BarbaraInternshipProject\\test\\Soni3.tif'
    print("Start processing image: " + image_url)
    ######--open image    
    IJ.run('Close All')
    IJ.run("ROI Manager...", "")
    aRoiManager = RoiManager.getInstance()
    if aRoiManager is not None:
        aRoiManager.reset()
    #jimage = ij.io().open(image_url)
    #image = ij.py.from_java(jimage) #failed for local
    #ij.py.show(image, cmap='gray') # skip
    #open using ij core command instead.
    ips = IJ.openImage(image_url)
    ips_raw = ips.duplicate()
    ips.show()
    IJ.run("Set Scale...", "distance=0 known=0 pixel=1 unit=pixel");
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
    aGaussianBlur.blur(ip,GaussSigma) 
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
    IJ.setAutoThreshold(ips,aThresholdMtd);# can also hand0adjust instead of running code for finer ctrl
    name = input('******Please see if threshold is ok, you can Edit-Adjust threshold-further adjust(but do not click apply), then input anything into console and press enter to go on \n*********')
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
    #aRois = aRoiManager.getROIs()
    nRoiCount = aRoiManager.getCount();
    IJ.run("Colors...", "foreground=white background=black selection=yellow");
    ######--Cycle go through all Roi
    PFF_RoiAss = []
    PFFclump_RoiAss = []
    for iRoi in range(nRoiCount):
        aRoi = aRoiManager.getRoi(iRoi)
        PFFclump_RoiAss.append(aRoi)
    for iRoi in range(nRoiCount):
        # iRoi = 0
        aRoi = PFFclump_RoiAss[iRoi]
        # tell if to skip 
        aRoiStat = aRoi.getStatistics()
        #aRoiStat.area
        aFraction = aRoiStat.areaFraction
        if aFraction > 98.5: # scale bar is rectangle with hextreme high areaFraction ~100
            continue
        # make a copy of ips_particleMask destined for current roi w/o contanimation at corner(still risky, better make canvar bounds black)
        ips_aRoiSacrifice = ips_particleMask.duplicate()
        # click one ROI from roiManager to activate onto current mask image:
        ips_aRoiSacrifice.setRoi(aRoi)
        ips_aRoiSacrifice_crop = ips_aRoiSacrifice.crop()
        aRoiPath = os.path.splitext(image_url)[0]+'_'+ str(iRoi) +"_Roi.png"
        IJ.save(ips_aRoiSacrifice_crop,aRoiPath)
        ips_aRoiSacrifice_crop.changes = False
        ips_aRoiSacrifice_crop.close()
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
        if len(aXs)==4:
            continue # skip the rectangle scale bar
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
        nGiveup = 0;
        aSkipAss = [];
        break_level2 = 0;
        rightHalfFutureLRposAss = []
        rightHalfFutureaMinAss = []
        while True:
            scheduled = 0;
            if break_level2 == 1:
                break
            if done == 1:
                break
            aLen = len(hXs_growing);
            #print("Enter a session for Seg cruising with segments: " + str(aLen))
            for iSeg in range(aLen):
                #print(str(iSeg))
                # its not good to fracture at same site too many times
                if iSeg in aSkipAss:
                    if iSeg==len(hXs_growing)-1:
                        done = 1;
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
                    #print("a small seg @<" + str(iSeg) + "/" + str(len(hXs_growing)-1) + ">time " +str(time.time()))
                    # edge is small, No need shrink
                    if iSeg==len(hXs_growing)-1:
                        done = 1;
                    continue
                else:
                    nGiveup = nGiveup + 1
                    #print(nGiveup)
                    if nGiveup>nGiveupMax:
                        break_level2 = 1;
                        break
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
                    if [(aStartX,aStartY),(aEndX,aEndY)] in rightHalfFutureLRposAss:
                        aMinHit = rightHalfFutureaMinAss[rightHalfFutureLRposAss.index([(aStartX,aStartY),(aEndX,aEndY)])]
                        scheduled = 1
                    else:
                        aMinHit = np.where(np.amin(aDists)==aDists)[0][0]
                    # empty is : len(np.where(np.amin(aDists)==786756.67)[0])==0
                    # ************************************************        
                    # ****** update for multiple filters start*******
                    # ************************************************        
                        # filter 2: 
                             # determine if the distance [aSegMid ~ aMinhit] is larget than [aStart ~ aSegMid].
                                 # if larger, then should skip this fracture event.
                                 # if smaller, clearance.
                    aDiameter = ((aXs[aMinHit]-aSegMidX)**2+(aYs[aMinHit]-aSegMidY)**2)**0.5
                    aSegLen = ((aEndX-aStartX)**2+(aEndY-aStartY)**2)**0.5
                    if aDiameter > aSegLen*0.5 + aDiameterBuff:
                        aSkipAss.append(iSeg)
                        continue
                         # filter 3: 
                             # determine if the point aMinhit is also a vertex of rawRoi.(can prevent some on-edge pseudo-fragmented roi sideline)
                    if np.amin(aDists) == 0:
                        aSkipAss.append(iSeg)
                        continue
                            # determine if the point aMinhit is belongs to one point of real-time convexHull vertex.
                    aOnContourXHits = np.where(aXs[aMinHit]==hXs_growing)[0]
                    aOnContourYHits = np.where(aYs[aMinHit]==hYs_growing)[0]
                    if len(aOnContourXHits)>0 and len(aOnContourYHits)>0:
                        if len(np.intersect1d(aOnContourXHits,aOnContourXHits))>0:
                            aSkipAss.append(iSeg)
                            continue
                            # determine if current iSeg is also one seg of rawRoi
                    aStartOnRawRoiXHits = np.where(aStartX==aXs)[0]
                    aStartOnRawRoiYHits = np.where(aStartY==aYs)[0]
                    aStartOnRawRoiXYHits = np.intersect1d(aStartOnRawRoiXHits,aStartOnRawRoiYHits)
                    aEndOnRawRoiXHits = np.where(aEndX==aXs)[0]
                    aEndOnRawRoiYHits = np.where(aEndY==aYs)[0]
                    aEndOnRawRoiXYHits = np.intersect1d(aEndOnRawRoiXHits,aEndOnRawRoiYHits)
                    if len(aStartOnRawRoiXYHits)>0 and len(aEndOnRawRoiXYHits)>0:
                                # ...by comparing if aStartOnRawRoiXYHits and aEndOnRawRoiXYHits has annexed elements:
                        aStartOnRawRoiXYHits_shift1 = aStartOnRawRoiXYHits + 1;
                        aStartOnRawRoiXYHits_shift1_rgHt = np.where(aStartOnRawRoiXYHits_shift1==len(aXs))[0]
                        if len(aStartOnRawRoiXYHits_shift1)>0:
                            aStartOnRawRoiXYHits_shift1[aStartOnRawRoiXYHits_shift1_rgHt]=0
                        annex_ask = np.intersect1d(aStartOnRawRoiXYHits_shift1,aEndOnRawRoiXYHits)
                        if len(annex_ask)>0:
                            aSkipAss.append(iSeg)
                            continue
                            # detetmine if iSeg and any Segment of rawRoi share at least one point and same skew (can prevent much more on-edge pseudo-fragmented roi sideline)
                    if len(aStartOnRawRoiXYHits)>0 or len(aEndOnRawRoiXYHits)>0:
                        aStartEndOnRawRoiXYHitsUnion = np.union1d(aStartOnRawRoiXYHits,aEndOnRawRoiXYHits)
                        skipInRowAsk = 0
                        aSegSkew = np.inf
                        if (aEndX-aStartX) != 0:
                            aSegSkew = (aEndY-aStartY)/(aEndX-aStartX)
                        for iUnionPoints in aStartEndOnRawRoiXYHitsUnion:
                            aRawRoiSegSkew_F = np.inf
                            aRawRoiSegSkew_R = np.inf
                            if (aYs[iUnionPoints]-aXs[iUnionPoints]) != 0:
                                aRawRoiSegSkew_F = (aYs[np.mod(iUnionPoints+1,len(aXs))]-aXs[np.mod(iUnionPoints+1,len(aXs))])/(aYs[iUnionPoints]-aXs[iUnionPoints])
                            if (aYs[iUnionPoints-1]-aXs[iUnionPoints-1]) != 0:
                                aRawRoiSegSkew_R = (aYs[iUnionPoints]-aXs[iUnionPoints])/(aYs[iUnionPoints-1]-aXs[iUnionPoints-1])
                            if aRawRoiSegSkew_F == aSegSkew or aRawRoiSegSkew_R == aSegSkew:
                                skipInRowAsk = 1
                                break
                        if skipInRowAsk:
                            aSkipAss.append(iSeg)
                            continue
                        # filter 0:
                            # see end.
                        # filter 1:
                            #Fracture event in aMinHit has risk of letting some points tresspass the just-formed half-arm from sweeping from [aStart ~ aSegMid] to [aStart ~ aMinhit]
                            # need to identify these points, and pick the point that tresspass at farthest [relative? or absolute?]extrude.
                            # treat this point as the fracture instead!
                            # threotically, relative extrude should be considered in the triangle~radiation context.
                            # but because imagej's detected ROI is pixel-wise, not as imaris's vector-wise, thus the near-ending corner points always has ~100% relative extrude in triangle just because it speaks loudest, which is unwanted.
                            # this question is equal to the question of select all points 
                                # and ask if exist one point meet all the 3 conditions:
                                    # condition 1: this point must located inside leftHalfTriangle: [aStart,aSegMid,aMinHit]
                                    # condition 2: this point must has distance to the line [aStart ~ aMinHit] largest among all the points meet condition 1
                                    # condition 3: this point must has distance to the line [aStart ~ aMinHit] that beyong a tiny threshold like 3 or 4
                                        # this is because in pixel-wise roi, there must exist a few "near-ending corner points" that just cross-line, thus definitely meet condition 1.
                                            # if no other significant extrusion exist elsewhere, one of these "near-ending corner points" will definitely pass condition 2
                                            # so condition 3 is necessay to block these points to be false positively selected.
                               # if such point exsit, must divert to these kinds of points.
                               # if such point not exist, then goto filter 2.
                               # someone may ask why not directly pick the nearest point to edge instead of using midPpint to search?
                                   # this alternative way might work in imaris vector-style points.
                                   # but for imagej's voxel-style extreme-dense roi, this alternative way will make each fracture a very tiny shift because the point near edgeEnd is definetely most close to edge.
                                       # thus for imagej's pixelStyle, must use midPoint to search for hits.
                    # select vertex from [aXs,aYs] that located inside triangle [aStartX,aStartY], [aXs[aMinHit],aYs[aMinHit]],[aSegMidX,aSegMidY]
                    if scheduled==0:
                        aXYsInsideLeftTriangleHitsAss = []
                        aXYsInsideLeftTriangleExtDistAss = []
                        for iVtx in range(len(aXs)): # find insider triangle
                            if PointInTriangle((aXs[iVtx],aYs[iVtx]),[(aStartX,aStartY),(aXs[aMinHit],aYs[aMinHit]),(aSegMidX,aSegMidY)]) == 1:
                                # measure distance of insiders to line (aStartX,aStartY) ~ (aXs[aMinHit],aYs[aMinHit])
                                dist = np.linalg.norm(np.cross(np.array([aXs[aMinHit],aYs[aMinHit]])-np.array([aStartX,aStartY]),np.array([aStartX,aStartY])-np.array([aXs[iVtx],aYs[iVtx]])))/ \
                                                      np.linalg.norm(np.array([aXs[aMinHit],aYs[aMinHit]])-np.array([aStartX,aStartY]))
                                if np.abs(dist)>inTriExtruDistMinThresh:
                                    aXYsInsideLeftTriangleHitsAss.append(iVtx)
                                    aXYsInsideLeftTriangleExtDistAss.append(np.abs(dist))
                        if len(aXYsInsideLeftTriangleExtDistAss)>0:
                            aMaxExtHit = np.where(np.amax(aXYsInsideLeftTriangleExtDistAss)==aXYsInsideLeftTriangleExtDistAss)[0][0]
                            aMaxExtaXYsHit = aXYsInsideLeftTriangleHitsAss[aMaxExtHit]
                            aMinHit = aMaxExtaXYsHit
                        # filter 0:
                                # if the fracture event get clearance, it is also necessary now to detect trespass event in the rightHalfTriangle.
                                    # if there is no tresspass event, go on
                                    # if there is trespass event, also search for the point of most significant absolute pointB
                                        # and memory matrix of (begin:aMidHit,bypass:pointB,stop:aEnd).
                                        # in fact for everycycle, there is a filter 0 in the most beginning but I describe it here:
                                            # for the current edge to be fracture,does the begin/stop pair match one of the record in memory list?
                                                # if no match, then go filter 1.
                                                # if match, then use the matched middle pointB as aMidHit, and skip filter, and go filter 2, 3,...
                                                # this filter must be used because the righdHalfEdge has no direct memory of whether its last fracture history..
                                                    # ...that born this righdHalfEdge has trespass event in rightHalfTriangle or not.
                        # !!!...note that aMinHit has just ben updated!!!!
                        aXYsInsideRightTriangleHitsAss = []
                        aXYsInsideRightTriangleExtDistAss = []
                        for iVtx in range(len(aXs)): # find insider triangle
                            if PointInTriangle((aXs[iVtx],aYs[iVtx]),[(aEndX,aEndY),(aXs[aMinHit],aYs[aMinHit]),(aSegMidX,aSegMidY)]) == 1:
                                # measure distance of insiders to line (aStartX,aStartY) ~ (aXs[aMinHit],aYs[aMinHit])
                                dist = np.linalg.norm(np.cross(np.array([aXs[aMinHit],aYs[aMinHit]])-np.array([aEndX,aEndY]),np.array([aEndX,aEndY])-np.array([aXs[iVtx],aYs[iVtx]])))/ \
                                                      np.linalg.norm(np.array([aXs[aMinHit],aYs[aMinHit]])-np.array([aEndX,aEndY]))
                                if np.abs(dist)>inTriExtruDistMinThresh:
                                    aXYsInsideRightTriangleHitsAss.append(iVtx)
                                    aXYsInsideRightTriangleExtDistAss.append(np.abs(dist))
                        if len(aXYsInsideRightTriangleExtDistAss)>0:
                            aMaxExtHit = np.where(np.amax(aXYsInsideRightTriangleExtDistAss)==aXYsInsideRightTriangleExtDistAss)[0][0]
                            aMaxExtaXYsHit = aXYsInsideRightTriangleHitsAss[aMaxExtHit]
                            rightHalfFutureLRposAss.append([(aXs[aMinHit],aYs[aMinHit]),([aEndX,aEndY])])
                            rightHalfFutureaMinAss.append(aMaxExtaXYsHit)
                    # ************************************************                            
                    # ****** update for multiple filters finish******* 
                    # ************************************************        
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
        ips_aRoiSacrifice.changes = False
        ips_aRoiSacrifice.close()
        ips_aRoiShrink.show()
        aShrinkRoi.setLocation(aBaseX,aBaseY)
        ips_aRoiShrink.setRoi(aShrinkRoi)  # Uh??? roi moved to upperleft corner! solved by upper line aBaseXY.
        ip_aRoiShrinkMask = ips_aRoiShrink.createRoiMask();
        ips_aRoiShrinkMask = ImagePlus("shrinkedOuterMask",ip_aRoiShrinkMask)
        ips_aRoiShrinkMask.show()
        # name = input('******Please Enter 1 to proceed \n*********')
        ######--do a further erode of shrinked roi's mask to further miniate the tiny margins that might contaminate in the final result
        for i in range(int(nErode)):
            IJ.run(ips_aRoiShrinkMask, "Erode", "");
        ######--remove roi from ips_aRoiSacrifice, then invert image
        IJ.run(ips_aRoiShrink, "Select None", "");
        IJ.run(ips_aRoiShrink, "Invert", "");
        ######--multiply ips_aRoiSacrifice to ips_aRoiShrink
        aImageCalculator = ImageCalculator();
        ips_PFF = aImageCalculator.run("Multiply create", ips_aRoiShrink, ips_aRoiShrinkMask)
        ips_aRoiShrink.changes = False
        ips_aRoiShrink.close()
        ips_aRoiShrinkMask.changes = False
        ips_aRoiShrinkMask.close()
        ips_PFF.show()
        #name = input('******Please Enter 1 to proceed \n*********')
        ######--remove very tiny dots that not PFF, (can also set to remove extreme large objects which might be fully closed background area by PFF)
        IJ.run(ips_PFF, "Analyze Particles...", "size=20-Infinity show=Masks clear") # no add !!!
        pffMaskTitle = "Mask of " + str(ips_PFF.getTitle())
        ips_PFF.changes = False
        ips_PFF.close()
        ips_PFFtrim = WindowManager.getImage(pffMaskTitle);
        IJ.run(ips_PFFtrim, "Grays", "");
        ######--get Perimeter & Area of all PFF in this tile
        if True:
            # -method is not correct
            ips_PFFerode = ips_PFFtrim.duplicate();
            IJ.run(ips_PFFerode, "Erode", "");
                #a = ips_PFF.getProcessor().getPixels()
                #b = int(a[1])
                #c = ctypes.c_uint8(-5)
                #d = c.value
            # to reduce the cost of pixel count, crop a intermediate file now:
            ips_PFFtrim.setRoi(hRoi)
            ips_PFFtrim_crop = ips_PFFtrim.crop();
            ips_PFFerode.setRoi(hRoi)
            ips_PFFerode_crop = ips_PFFerode.crop();
            ips_PFFerode.changes = False
            ips_PFFerode.close()
            aMatrix_PFF = javaArray_to_npArray(ips_PFFtrim_crop.getProcessor().getPixels()) #<java array 'byte[]'>
            ips_PFFtrim_crop.changes = False
            ips_PFFtrim_crop.close()
            aMatrix_PFF2 = javaArray_to_npArray(ips_PFFerode_crop.getProcessor().getPixels()) #<java array 'byte[]'>
            ips_PFFerode_crop.changes = False
            ips_PFFerode_crop.close()
            PFF_perimeter = ((aMatrix_PFF.sum() - aMatrix_PFF2.sum())/255)*pixel_nm
            PFF_area = (aMatrix_PFF.sum()/255)*pixel_nm*pixel_nm
        else:
            # -use native Area and Perim. table
            IJ.run("Clear Results", "");
            IJ.run(ips_PFFtrim, "Measure", "");
            aResultsTable = ResultsTable.getResultsTable()
            aResultImg = aResultsTable.getTableAsImage()
                # should get float, but read the return 4 bytes of this float as a int32. So need cast int32 to single(32-bit float)
            aPixelValue = aResultImg.getPixel(int(idxCol_length),0)
            #aResultsTable.getColumnIndex('Minor') #why not corrct? stranges of 0-1-4-5-10- -1- -1
            singleBytes = aPixelValue.to_bytes(4,'little')
                #singleBytes = int(aResultImg.getPixel(10,0)).to_bytes(4,'little')
            PFF_perimeter = (struct.unpack('<f',singleBytes))[0]
            aAreaValue =  aResultImg.getPixel(int(idxCol_area),0)
            singleBytes = aAreaValue.to_bytes(4,'little')
            PFF_area = (struct.unpack('<f',singleBytes))[0]
        
        PFF_perimeter_area_ratio = PFF_perimeter/PFF_area
        print("PFF_perimeter_ = " + str(PFF_perimeter))
        print("PFF_area = "+ str(PFF_area))
        print("PFF_perimeter_area_ratio = "+ str(PFF_perimeter_area_ratio))
        ######--get isoLength and isoHeight for current PFF tile
        PFF_isoLenSum = (PFF_perimeter + (PFF_perimeter**2 - 16*PFF_area)**0.5)/4
        PFF_isoThick = (PFF_perimeter - (PFF_perimeter**2 - 16*PFF_area)**0.5)/4
        print("PFF_isoLenSum = " + str(PFF_isoLenSum))
        print("PFF_isoThick = " + str(PFF_isoThick))
        ######--detect PFF's roi
        ic = ImageConverter(ips_PFFtrim);
        ic.convertToGray8();
        ips_PFFtrim.updateAndDraw();
        # ----temporary debug that a pre-threshold can solve bounding box roi problem
        IJ.setAutoThreshold(ips_PFFtrim, "Default dark");
        #ips_PFFtrim2 = ips_PFFtrim.duplicate()
        ip_PFFtrim = ips_PFFtrim.createThresholdMask() # echo ip_mask then we know its a ip type, thus swap to overwrite the ips_mask which is from copy of ips
        ips_PFFtrim.setProcessor(ip_PFFtrim)
        #ips_PFFtrim2.show()
        #ips_PFFtrim = ips_PFFtrim2
        # ---debug finished
        IJ.run(ips_PFFtrim, "Create Selection", ""); # bug: the imafe border was also selected as a large roi
        PFF_roi = ips_PFFtrim.getRoi()
        if PFF_roi is None:
            continue
        PFF_RoiAss.append(PFF_roi)
            # PFF_roi defines the exact contour of PFF materials on this PFF cluster on TEM images
        ######--Overlay PFF roi on raw image
        ips_raw_defer = ips_raw.duplicate()
        ips_raw_defer.setRoi(PFF_roi)
        ips_raw_defer.show() #MUST show to add visible overlay?? no
        #name = input('**********************************Please Enter 1 to proceed \n*********')
        IJ.run(ips_raw_defer, "Add Selection...", ""); #add active roi as overlay
        # crop this tile
        ips_raw_defer.setRoi(hRoi)
        ips_raw_defer_crop = ips_raw_defer.crop();
        ips_raw_defer.changes = False
        ips_raw_defer.close()
        ips_raw_defer_crop.show()
        #name = input('**********************************Please Enter 2 to proceed \n**********')
        aTilePngPath = os.path.splitext(image_url)[0]+ '_' + str(iRoi) +"_RoiOverlay.png"
        aROIPath = os.path.splitext(image_url)[0]+ '_' + str(iRoi) + "_Roi.roi"
        IJ.save(ips_raw_defer_crop,aTilePngPath)
        RoiEncoder.save(PFF_roi,aROIPath)
        ######--get most fitted ellipsoid major and minor length: not reliable! deprecated!
        IJ.run("Clear Results", "");
        IJ.run(ips_PFFtrim, "Measure", "");
        aResultsTable = ResultsTable.getResultsTable()
        aResultImg = aResultsTable.getTableAsImage()
            # should get float, but read the return 4 bytes of this float as a int32. So need cast int32 to single(32-bit float)
        aPixelValue = aResultImg.getPixel(int(idxCol_minorEllipsoid),0)
        #aResultsTable.getColumnIndex('Minor') #why not corrct? stranges of 0-1-4-5-10- -1- -1
        singleBytes = aPixelValue.to_bytes(4,'little')
            #singleBytes = int(aResultImg.getPixel(10,0)).to_bytes(4,'little')
        PFF_EllipsoidMinorLen = (struct.unpack('<f',singleBytes))[0]   #little endian. test Correct!
            # struct.unpack('>f', singleBytes) #big endian
            # ctypes.c_float(int(aPixelValue)) #wrong! soft conversion, not hard typecast!
        # rough estimation of how many parallel PFF filaments in this PFF cluster
        PFF_nCollate = PFF_EllipsoidMinorLen/PFF_isoThick
        # rough estimation of mean length of individual PFF filaments in this PFF cluster
        PFF_FragIsoLen = (PFF_isoLenSum/PFF_nCollate)
        print("PFF_EllipsoidMinorLen = " + str(PFF_EllipsoidMinorLen))
        print("PFF_nCollate = " + str(PFF_nCollate))
        print("PFF_FragIsoLen = " + str(PFF_FragIsoLen))
        ######--mask TEM by ips_PFFtrim then detect ridge
        if True:
            if True: # use image calculator
                ips_PFFtrimUnit = ips_PFFtrim.duplicate()
                ips_PFFtrimUnit.setRoi(hRoi)
                ips_PFFtrimUnitCrop = ips_PFFtrimUnit.crop();
                ips_PFFtrimUnitCrop.show()
                IJ.run(ips_PFFtrimUnitCrop, "Divide...", "value=255");
                ips_raw_defer_crop_masked = aImageCalculator.run("Multiply create", ips_PFFtrimUnitCrop, ips_raw_defer_crop);
                ips_PFFtrimUnitCrop.changes = False
                ips_PFFtrimUnitCrop.close()
            else: # use cear outside.GUI not stable
                PFF_roi2 = PFF_roi.clone()
                ips_raw_defer_crop_masked = ips_raw_defer_crop.duplicate()
                PFF_roi2.setLocation(PFF_roi.getXBase()-aBaseX,PFF_roi.getYBase()-aBaseY) #correct Hull and shrinkRoi baseXY offset
                ips_raw_defer_crop_masked.setRoi(PFF_roi2)
                IJ.run(ips_raw_defer_crop_masked, "Clear Outside", "");
                IJ.run(ips_raw_defer_crop_masked, "Select None", "");
                ips_raw_defer_crop_masked.updateAndDraw()
            ips_raw_defer_crop.changes = False
            ips_raw_defer_crop.close()
            ips_raw_defer_crop_masked.show()
            IJ.run(ips_raw_defer_crop_masked, "Gaussian Blur...", "sigma=1");
            IJ.run("Clear Results", "");
            if aRoiManager is not None:
                aRoiManager.reset()
            # displayresults add_to_manager 
            aOption = "line_width=3.5 high_contrast=230 low_contrast=87 method_for_overlap_resolution=SLOPE sigma=1.51 lower_threshold=3.06 upper_threshold=7.99 minimum_line_length=10 maximum=0"
            if False:
                IJ.run(ips_raw_defer_crop_masked, "Ridge Detection",aOption);#loading failed
            else:
                Macro.setOptions(aOption)
                aLinesObj = Lines()
                aLinesObj.setup('',ips_raw_defer_crop_masked)
                aLinesObj.displayResults = False
                aLinesObj.showIDs = False
               # aLinesObj.addToRoiManager = False #failed because fiels/method same name,field is private, but I switch to public thus confliet. Can access as method only.
                ip_raw_defer_crop_masked = ips_raw_defer_crop_masked.getProcessor()
                try:
                    aLinesObj.run(ip_raw_defer_crop_masked) #failed? no error and no response? already processed! Haha
                except:
                    continue
                Macro.setOptions('')
                #aLinesObj.addToRoiManager = False;
                aLinesObj.setup('final',ips_raw_defer_crop_masked)
                if aRoiManager is not None:
                    aRoiManager.reset()
                LineAss = aLinesObj.result[0] #recompiled, add public
                aLineLenAss = []
                for iLine in range(LineAss.size()):
                    aLine = LineAss.get(iLine)
                    aLineLenAss.append(aLine.estimateLength()*pixel_nm)
                #IJ.run(ips_raw_defer_crop_masked, "Add Selection...", ""); #add active roi as overlay
                aTilePngPath = os.path.splitext(image_url)[0]+ '_' + str(iRoi) +'_RoiCrop_Ridge.png'
                IJ.run("Clear Results", ""); #anyway, I can still clear roiManager to fight against aLinesObj.addToRoiManager
                IJ.save(ips_raw_defer_crop_masked,aTilePngPath)
                ips_raw_defer_crop_masked.changes = False
                ips_raw_defer_crop_masked.close()
                #### export length details
                aCsvPath = os.path.splitext(image_url)[0]+'_'+ str(iRoi) + '_RoiCrop_Ridge.csv'
                with open(aCsvPath, 'w', newline='') as csvfile:
                    spamwriter = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    for iNum in range(len(aLineLenAss)):
                        spamwriter.writerow([str(aLineLenAss[iNum])])
        ##### close essential ips        
        ips_PFFtrim.changes = False
        ips_PFFtrim.close(); # must close now to avoid name conflict for next roi
        #### export current roi tile data as csv file
        aCsvPath = os.path.splitext(image_url)[0]+'_'+ str(iRoi) + '_RoiClump.csv'
        # note that arg1st for open must be r-strings instead of common strings!
        with open(aCsvPath, 'w', newline='') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
            spamwriter.writerow(['PFF_perimeter',PFF_perimeter])
            spamwriter.writerow(['PFF_area',PFF_area])
            spamwriter.writerow(['PFF_perimeter_area_ratio',PFF_perimeter_area_ratio])
            spamwriter.writerow(['PFF_isoLenSum',PFF_isoLenSum])
            spamwriter.writerow(['PFF_isoThick',PFF_isoThick])
            spamwriter.writerow(['PFF_nCollate',PFF_nCollate])
            spamwriter.writerow(['PFF_FragIsoLen',PFF_FragIsoLen])
            spamwriter.writerow(['PFF_EllipsoidMinorLen',PFF_EllipsoidMinorLen])
            
    ###---overlay all PFF_roi on raw image
    ips_raw_defer = ips_raw.duplicate()
    ips_raw_defer.show() #MUST show to add visible overlay?? no
    for PFF_roi in PFF_RoiAss:
        ips_raw_defer.setRoi(PFF_roi)
        IJ.run(ips_raw_defer, "Add Selection...", "");
        #name = input('******Please Enter 1 to proceed \n*********')
    aTilePngPath = os.path.splitext(image_url)[0]+"_RoiCrop_All.png"
    IJ.save(ips_raw_defer,aTilePngPath)
    #IJ.run('Close All')
    
##################--main-#####################
rtFolder = "D:\\Lab\\LKC\\BarbaraInternshipProject\\test";
if not os.path.isdir(rtFolder):
    rtFolder = uigetdir('Select a folder having images to analysis')
print(rtFolder);os.chdir(rtFolder)
for file in glob.glob("*"+aFmt):
    image_url = rtFolder+'\\'+file
    process_one_image(image_url)