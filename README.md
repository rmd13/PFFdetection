# PFFdetection.py
detect contour of  sonicated PFF( α-syn preformed fibril) on TEM images

```
Installzation
    #1. install Fiji from https://downloads.imagej.net/fiji/latest/fiji-win64.zip
        install Python3.6.6 from https://www.python.org/ftp/python/3.6.6/python-3.6.6.exe
        install spyder3.3.1 by commands  'pip install spyder==3.3.1' into command window.
        place ij_ridge_detect-1.4.0-J6Public.jar inside Fiji's installation .\Plugins folder.
        instalL OpenJDK8  https://cdn.azul.com/zulu/bin/zulu8.54.0.21-ca-fx-jdk8.0.292-win_x64.zip
            unzip to a folder like D:\GreenSoft\zulu8.54.0.21-ca-fx-jdk8.0.292-win_x64 and add to windows environment 'Path'.
        install maven https://downloads.apache.org/maven/maven-3/3.8.1/binaries/apache-maven-3.8.1-bin.zip
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
  ```  
    
![image](https://user-images.githubusercontent.com/22294036/138417196-84b377da-3218-4114-a7b8-2cbd50c939e0.png)

![image](https://user-images.githubusercontent.com/22294036/137282608-c3ad8fee-b4a0-4f2d-a3da-3057f5494965.png)

![image](https://user-images.githubusercontent.com/22294036/137282738-cf812845-3fb5-4dd6-a262-b5c69127920a.png)

![image](https://user-images.githubusercontent.com/22294036/129352315-011cbee9-7fd8-4881-b62a-7a8f34a7c2c1.png)

![image](https://user-images.githubusercontent.com/22294036/129352406-4981fe1a-4b70-4bc2-b2b4-b3cbd6ee76de.png)

