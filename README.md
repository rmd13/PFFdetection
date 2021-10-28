# PFFdetection.py
detect contour of  sonicated PFF( α-syn preformed fibril) on TEM images

```
    #1.Installization
        install Fiji:
            --way A1: (not suggested as API may change in future, way 2 is better for compatibility)
                download and unzip from https://downloads.imagej.net/fiji/latest/fiji-win64.zip
                place ij_ridge_detect-1.4.0-J6Public.jar inside Fiji's installation .\Plugins folder.
            --way A2:(suggested, tested stable)
                download from this repo which already has ij_ridge_detect-1.4.0-J6Public.jar included.
        
        install python and spyder3 (and pyimagej by way 2)
            --way B1:(not suggested) prone to error/fail because of updates in pywin32 in 2021.
                install Python3.6.6 from https://www.python.org/ftp/python/3.6.6/python-3.6.6-amd64.exe
                install spyder3.3.1 by commands 'pip install spyder==3.3.1' into command window.
                
            --way B2:(suggested) download the python zip file Python36.rar containig both python, Spyder3 and pyimagej.
                unzip as 'C:\\Users\~\AppData\Local\Programs\Python\Python36\...'
                then add 'C:\\Users\~\AppData\Local\Programs\Python\Python36\Scripts' to environment Path
                then open 'C:\\Users\~\AppData\Local\Programs\Python\Python36\Scripts\spyder3.exe' in notepad++(download if not have)
                    find string 'rmd', you will locate to a path 
                    update the path including updating 'rmd' to your path equivalents of username, then save the file.
        
        instalL OpenJDK8
            https://cdn.azul.com/zulu/bin/zulu8.54.0.21-ca-fx-jdk8.0.292-win_x64.zip
            unzip to a folder like D:\GreenSoft\zulu8.54.0.21-ca-fx-jdk8.0.292-win_x64 and add to windows environment 'Path'.
        
        install maven 3.8.1 or 3.8.3
            visit https://maven.apache.org/download.cgi
                or https://downloads.apache.org/maven/maven-3/3.8.1/binaries/apache-maven-3.8.1-bin.zip
            unzip to a folder like D:\GreenSoft\apache-maven-3.8.1\bin
            add  folder like 'D:\\GreenSoft\apache-maven-3.8.1\bin' to windows environment 'Path'.
            test by running <mvn -v>. Note JAVA_HOME is required.
            if no java installed:
                either install a java jre or jdk such as install jdk as C:\Program Files\Java\jdk1.8.0_211
                or just use the java inside Fiji such as: D:\GreenSoft\Fiji.app52p\java\win64\jdk1.8.0_172

        install pyimagej if pyimagej has not been installed (in --way B1).
            by commands 'pip install pyimagej' into windows command window.
        
    #2. Run imagej, click Analyze-Set Measurement..., tick as image blow shows, then quit.
    
    #3. launch spyder3q GUI by input 'spyder3.exe' into command window and press enter.
        it usually localized in 'C:\\Users\~\AppData\Local\Programs\Python\Python36\Scripts\spyder3.exe'
        
    #4. Open the newest version of script myPFFdetection(largest number).py in spyder3.
            edit the line in this script to change to your local Fiji application path.
                FijiAppPath = r"D:\\GreenSoft\\Fiji.app52p" # Fiji installation path
            
    # then run the whole script in Spyder3.
        # note, the first run may take time to auto-download supporting files..
        # after Fiji panel pop up, run this script again to start processing images.
        
  ```  
    
![image](https://user-images.githubusercontent.com/22294036/138417196-84b377da-3218-4114-a7b8-2cbd50c939e0.png)

![Measure](https://user-images.githubusercontent.com/22294036/139278999-cbd49769-7aa4-49b9-b132-9c751c283dee.png)

[image](https://user-images.githubusercontent.com/22294036/137282608-c3ad8fee-b4a0-4f2d-a3da-3057f5494965.png)

[image](https://user-images.githubusercontent.com/22294036/137282738-cf812845-3fb5-4dd6-a262-b5c69127920a.png)

[image](https://user-images.githubusercontent.com/22294036/129352315-011cbee9-7fd8-4881-b62a-7a8f34a7c2c1.png)

[image](https://user-images.githubusercontent.com/22294036/129352406-4981fe1a-4b70-4bc2-b2b4-b3cbd6ee76de.png)

