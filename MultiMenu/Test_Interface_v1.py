# -*- coding: utf-8 -*-

# Modules for main menu
import ctypes, functools, multiprocessing, numpy, os, re, sys, time, Tkinter,\
       tkFileDialog, ttk

# Append python file path to system path for access to tools folder
toolsFolder = os.path.join(os.path.dirname(sys.argv[0]), "Tools")
sys.path.append(toolsFolder)

################################################################################
# Class object
class MultiMenu:
    # Initializer
    def __init__(self):
        # Toplevel cancel boolean
        self.toolMenuCanceled = False
        
        # CPU resource variables
        self.cpuThreadCount = multiprocessing.cpu_count()
        self.cpuTrackers = []
        self.cpuEntries = []
        self.CPUEntryVar = None
        self.CPUMainEntry = None

        # Image types allowed
        self.allowedImageFormats = ['kap','jp2','jpg','tif','iff']

        # Create the manager queue instance
        self.manager = multiprocessing.Manager()
        self.resultsQueue = self.manager.Queue()

        # Tools found in tool folder
        self.toolsFoundRaw = [re.search(r'(.*?)\.', x).group(1) \
                           for x in os.listdir(toolsFolder)\
                           if x.endswith('.py')]
        self.toolsFoundFiltered = [re.search(r'[\d]*([\w\d-]*)', x).group(1)\
                                   for x in os.listdir(toolsFolder)\
                                   if x.endswith('.py')]
        self.toolsDictionary = dict(zip(self.toolsFoundFiltered,
                                        self.toolsFoundRaw))
        
        # List of killed tasks
        self.killedTasks = []

        # List of completed tasks
        self.completedTasks = []

        # Tkinter root instance
        self.root = Tkinter.Tk()

        # Initiate GUI update routine
        self._updateGUI()

        # Messagebox call
        self.messageBox = ctypes.windll.user32.MessageBoxA

        # Messagebox dictionary
        self.messageBoxDictionary = {'ABORTRETRYIGNORE':0x00000002L,
                                     'CANCELRETRYCONTINUE':0x00000006L,
                                     'HELP':0x00004000L,
                                     'OK':0x00000000L,
                                     'OKCANCEL':0x00000001L,
                                     'RETRYCANCEL':0x00000005L,
                                     'YESNO':0x00000004L,
                                     'YESNOCANCEL':0x00000003L,
                                     'EXCLAMATION':0x00000030L,
                                     'INFORMATION':0x00000040L,
                                     'WARNING':0x00000030L,
                                     'ASTERISK':0x00000040L,
                                     'QUESTION':0x00000020L,
                                     'STOP':0x00000010L,
                                     'ERROR':0x00000010L,
                                     'HAND':0x00000010L}

    # Class Function: Create menu for choosing tools to populate multi menu
    def _callToolMenu(self, notebook):
        # Top level
        topLevel = Tkinter.Toplevel()
        topLevel.title("Tool Loader")
        
        # Put toplevel above all other widgets
        topLevel.attributes('-topmost', True)

        # Configure column weights
        for x in range(4):
            topLevel.columnconfigure(x, weight = 1)

        # Configure row weights
        for x in range(4):
            topLevel.rowconfigure(x, weight = 1)

        # Tool menu description
        toolText = 'Tools available in the tool folder.'
        toolMenuLabel = Tkinter.Label(topLevel,
                                      text = toolText)
        toolMenuLabel.grid(column = 0, columnspan = 2,
                           row = 0, sticky = Tkinter.W)

        # Tool list box
        toolsListBox = Tkinter.Listbox(topLevel,
                                       height = 5,
                                       width = 15,
                                       selectmode = Tkinter.EXTENDED,
                                       state = Tkinter.NORMAL)
        toolsListBox.grid(column = 0, columnspan = 2, row = 1,
                          sticky = (Tkinter.W, Tkinter.E))

        # Insert tools found in tools list box
        self.toolsFoundRaw.sort() # sort the tools list
        for tool in self.toolsFoundRaw:
            toolsListBox.insert('end',
                                re.search(r'[\d]*([\w\d-]*)',
                                          tool).group(1))

        # Tool vertical scroll bar
        toolsVertScrollBar = Tkinter.Scrollbar(topLevel,
                                               orient=Tkinter.VERTICAL,
                                               command = toolsListBox.yview)
        toolsVertScrollBar.grid(column = 3, row = 1,
                          sticky = (Tkinter.N, Tkinter.S, Tkinter.W))

        # Tool horizontal scroll bar
        toolsHorScrollBar = Tkinter.Scrollbar(topLevel,
                                              orient = Tkinter.HORIZONTAL,
                                              command = toolsListBox.xview)
        toolsHorScrollBar.grid(column = 0, columnspan = 4, row = 2,
                          sticky = (Tkinter.W, Tkinter.S, Tkinter.E))

        # Set the X and Y scroll commands to the appropriate scroll bars
        toolsListBox['yscrollcommand'] = toolsVertScrollBar.set
        toolsListBox['xscrollcommand'] = toolsHorScrollBar.set

        # Toplevel functions
        def chooseTools():
            tabCount = 1
            toolSelection = toolsListBox.curselection()
            if len(toolSelection) != 0:
                for item in toolsListBox.curselection():
                    # Set tool name
                    toolName = toolsListBox.get(item)

                    # Set notebook tab name
                    setattr(self, 'tab' + str(tabCount),
                            Tkinter.Frame(notebook, name = toolName))

                    # Add notebook tab to 
                    notebook.add(getattr(self, 'tab' + str(tabCount)),
                                 text = toolName)

                    # Build tab menu
                    self._buildMenu(getattr(self, 'tab' + str(tabCount)))

                    # Increment tab count by 1
                    tabCount += 1

            # Quit top level menu
            topLevel.destroy()

        # Exit tool menu
        def exitToolMenu():
            self.toolMenuCanceled = True
            topLevel.destroy()
            self.root.destroy()

        # Ok button
        okButton = Tkinter.Button(topLevel, text = 'OK', width = 10,
                                  command = chooseTools)
        okButton.grid(column = 0, row = 3, sticky = Tkinter.W)       

        # Cancel button
        cancelButton = Tkinter.Button(topLevel, text = 'Cancel', width = 10,
                                      command = exitToolMenu)
        cancelButton.grid(column = 1, columnspan = 2, row = 3,
                          sticky = Tkinter.E)   

        # Maintain focus only on toplevel widget
        topLevel.grab_set()

        # Wait until toplevel widget closes to start main menu
        topLevel.wait_window()

    # Class Function: Update CPU Resources
    def _updateCPUResources(self):
        # Add up all currently selected cpu resources per tool
        # User should keep selected cpu resource count for each tool
        # at zero if they are not using it
        cpus = 0
        for cpu in self.cpuTrackers:
            cpus += int(cpu.get())

        # Control cpu comboboxes
        if cpus >= self.cpuThreadCount:
            for cpuCombo in self.cpuEntries:
                cpuCombo.config(values = [0])
        else:
            for cpuCombo in self.cpuEntries:
                cpuCombo.config(values = range(((self.cpuThreadCount - cpus) + 1)))

        # Update CPU resources label and combbox entries
        if self.CPUEntryVar != None or self.CPUMainEntry != None:
            cpuUpdateString = 'Number of CPUs available for tasking: [' \
                              + str(self.cpuThreadCount - cpus) + ']'
            self.CPUEntryVar.set(cpuUpdateString)
            self.CPUMainEntry.update()            
    
    # Function: Update the GUI with processing errors and results
    # http://code.activestate.com/recipes/82965-threads-tkinter-and-asynchronous-io/
    def _updateGUI(self):
        # Update CPU Resources
        self._updateCPUResources()
        
        # Function: Check completed tasks list
        def checkCompletedTasks(processName = None):
            # Closing procedures for completed tasks
            if len(self.completedTasks) > 0 or processName != None:
                for processName in self.completedTasks:
                    # Set display message 2 to complete
                    getattr(self, processName + 'Display')[2].set('100% Complete')
                    getattr(self, processName + 'Display')[3].update()

                    # Update progress bar to complete
                    getattr(self, processName + 'Progress')[0].set(100)
                    getattr(self, processName + 'Progress')[1].update()                 

                    # Terminate processes (cleanup processing)
                    for process in getattr(self, processName + 'ProcessList'):
                        getattr(self, processName + 'Display')[0].set(('Cleaning up ' + str(process.name)))
                        getattr(self, processName + 'Display')[1].update()
                        print str(process.name)
                        process.join(1)

                    # Enable process menu if finished
                    self._enableActionableWidgets(getattr(self, processName + 'WidgetList'))

                    # Display message that analyst ended process
                    getattr(self, processName + 'Display')[0].set((processName + ' completed.'))
                    getattr(self, processName + 'Display')[1].update()

                    # Enable reset button
                    getattr(self, (processName + "ResetButton")).config(state = Tkinter.NORMAL)
                    getattr(self, (processName + "ResetButton")).update()

                    # Enable log button
                    getattr(self, (processName + "LogButton")).config(state = Tkinter.NORMAL)
                    getattr(self, (processName + "LogButton")).update()

                    # Set ending time for process
                    setattr(self, (processName + "TimeEnded"), time.ctime())           

                    # Remove process name from completed list
                    self.completedTasks.remove(processName)

                    # Disable Kill Button
                    getattr(self, (processName + 'KillButton')).config(state = Tkinter.DISABLED)

        # Function: Check killed tasks list
        def checkKilledTasks(processName = None):
            # Closing procedures for killed tasks
            if len(self.killedTasks) > 0 or processName != None:
                # Killing process
                for processName in self.killedTasks:
                    # Terminate processes (cleanup processing)
                    for process in getattr(self, processName + 'ProcessList'):
                        getattr(self, processName + 'Display')[0].set(('Killing ' + processName))
                        getattr(self, processName + 'Display')[1].update()
                        process.terminate()
                        print process.name

                    # Update first display message
                    getattr(self, processName + 'Display')[0].set((processName + ' ended by analyst...'))
                    getattr(self, processName + 'Display')[1].update()

                    # Enable process menu if finished
                    self._enableActionableWidgets(getattr(self, processName + 'WidgetList'))

                    # Remove process name from killed list
                    self.killedTasks.remove(processName)

                    # Disable Kill Button
                    getattr(self, (processName + 'KillButton')).config(state = Tkinter.DISABLED)

        # Pull results from multiprocessing manager queue and update respective tabs
        while self.resultsQueue.empty() == False:
            # Grab presorted result from queue
            resultString = self.resultsQueue.get()

            # Determine which process is associated with result
            processName = re.search(r'(\w*Fix)', resultString).group(1)

            # Determine the errors and results list box elements
            errorsListBox = getattr(self, processName + 'ELB')
            resultsListBox = getattr(self, processName + 'RLB')

            # Progress variables
            progressValueVar = getattr(self, processName + 'Progress')[0]
            progressBar = getattr(self, processName + 'Progress')[1]

            # Display variables
            displayTextVar1 = getattr(self, processName + 'Display')[0]
            statusEntry1 = getattr(self, processName + 'Display')[1]
            displayTextVar2 = getattr(self, processName + 'Display')[2]
            statusEntry2 = getattr(self, processName + 'Display')[3]

            # Add error to error list box
            if "Error: " in resultString and processName in resultString:                
                # Increment error count by 1
                setattr(self, processName + 'ErrorCount', (getattr(self, processName + 'ErrorCount') + 1))

                # Add error to associated list box
                errorEntry = str(getattr(self, processName + 'ErrorCount')) + ': '+ ' | '.join(resultString.replace(processName, '').split('\t'))
                errorsListBox.insert('end', errorEntry)

            elif "Error: " not in resultString and processName in resultString:
                # Increment progress count + 1
                setattr(self, processName + 'ProgressCount', (getattr(self, processName + 'ProgressCount') + 1))              
                
                # Add result to associated list box
                resultEntry = str(getattr(self, processName + 'ProgressCount')) + ': '\
                              + ' | '.join(resultString.replace(processName, '').split('\t'))
                resultsListBox.insert('end', resultEntry)

            # Set progress bar integer
            assignedTasks = len(getattr(self, processName + 'AssignedTasks'))
            incompleteCount = assignedTasks - (getattr(self, processName + 'ProgressCount') + getattr(self, processName + 'ErrorCount'))

            # Check if process is complete
            if processName in self.completedTasks:
                # Check completed tasks list
                checkCompletedTasks(processName)

            # Check if process is ended by analyst
            elif processName in self.killedTasks:
                # Check killed tasks list
                checkKilledTasks(processName)
    
            # Progress handler
            elif incompleteCount == 0:                              

                # Add task to completed task list
                self.completedTasks.append(processName)

            # Once tasks are started begin printing status messages
            elif incompleteCount != 0 and incompleteCount != assignedTasks:
                # Update first message display with remaining tasks
                displayTextVar1.set(('Remaining tasks: ' + str(incompleteCount)))
                statusEntry1.update()

                # Update progress bar
                progressValueVar.set((getattr(self, processName + 'ProgressCount') + getattr(self, processName + 'ErrorCount')))
                progressBar.update()

                # Get int value of progress completed so far
                progressValue = int(round(float(assignedTasks - incompleteCount)/float(assignedTasks) * 100, 0))

                # Update second message
                displayTextVar2.set((str(progressValue) + '% Complete'))
                statusEntry2.update()
            else:
                displayTextVar1.set('Initializing converters...')
                statusEntry1.update()

        # Check killed tasks list
        checkKilledTasks()

        # Check completed tasks list
        checkCompletedTasks()
                    
        # After 100 milliseconds rerun update GUI
        self.root.after(100, self._updateGUI)

    # Class Function: Enable actionable widgets
    def _enableActionableWidgets(self, widgets):
        # Enable all actionable widgets
        for widget in widgets:
            if widget.widgetName == 'ttk::combobox':
                widget.config(state = 'readonly')
            elif widget.widgetName == 'button':                                        
                widget.config(state = Tkinter.NORMAL)
        
    # Class Function: List splitter
    def _chunkList(self, listObject, subLists):
        return numpy.array_split(numpy.array(listObject), subLists)

    # Class Function: Generic kill process
    def _killProcess(self, processName):
        # Set appropriate kill
        setattr(self, processName + 'KillBoolean', True)
        self.killedTasks.append(processName)

    # Class Function: Assign functions based on process chosen
    def _assignProcess(self,
                       menuFrame,
                       processName,
                       cpuStringVar,
                       justLogVar,
                       resultsKeyListBox,
                       errorsKeyListBox,
                       resultsListBox,
                       errorsListBox,
                       killButton,
                       progressValueVar,
                       progressBar,
                       displayTextVar1,
                       statusEntry1,
                       displayTextVar2,
                       statusEntry2,
                       resetButton,
                       logButton):

        # Retrieve cpus chosen by analyst
        cpusAllocated = int(cpuStringVar.get())
       
        # Only move forward if the analyst has selected at least one cpu
        if cpusAllocated > 0:            
            
            # Start loop for error processing
            while True:

                # Only process data if "task" [test keyword] is not in processname
                if 'task' not in processName:
                    processTest = False

                    # Get input folder
                    inputFolder = str(tkFileDialog.askdirectory(parent = menuFrame, title = "Please select an input folder."))
                    if inputFolder == '':
                        break

                    # Get output folder
                    outputFolder = str(tkFileDialog.askdirectory(parent = menuFrame, title = "Please select an output folder."))
                    if outputFolder == '':
                        break
                else:
                    inputFolder, outputFolder = 1, 2
                    processTest = True

                # Do not accept input folder as output folder
                # Do not accept no entry for either input or output folder
                if inputFolder != outputFolder and inputFolder != '' and outputFolder != '' or processTest == True:

                    # Clear results list box
                    resultsListBox.delete(0, Tkinter.END)
                    resultsListBox.update()

                    # Clear error list box
                    errorsListBox.delete(0, Tkinter.END)
                    errorsListBox.update()

                    # Clear first status message
                    displayTextVar1.set('')
                    statusEntry1.update()

                    # Clear second status message
                    displayTextVar1.set('')
                    statusEntry1.update()

                    # Create widget list that require disabling prior to processing
                    widgetList = [x for x in menuFrame.winfo_children()
                           if x.widgetName == 'ttk::combobox'
                           or x.widgetName == 'button']

                    # Disable all actionable widgets
                    for widget in widgetList:
                        widget.config(state = 'disabled')
                        widget.update()

                    # Build common environment variables
                    setattr(self, (processName + 'TimeStarted'), time.ctime())
                    setattr(self, (processName + 'AssignedTasks'), [])
                    setattr(self, (processName + 'ErrorCount'), 0)
                    setattr(self, (processName + 'ProgressCount'), 0)
                    setattr(self, (processName + 'WidgetList'), [])
                    setattr(self, (processName + 'ProcessList'), [])
                    setattr(self, (processName + 'RLB'), None)
                    setattr(self, (processName + 'ELB'), None)
                    setattr(self, (processName + 'Display'), None)
                    setattr(self, (processName + 'Progress'), None)
                    setattr(self, (processName + 'KillBoolean'), False)
                    setattr(self, (processName + 'KillButton'), killButton)
                    setattr(self, (processName + 'ResetButton'), resetButton)
                    setattr(self, (processName + 'LogButton'), logButton)

                    # Set up assigned task list variable
                    objectList = []

                    # Import process module
                    module = __import__(self.toolsDictionary[processName])

                    # Retrieve results key
                    setattr(self, (processName + 'ResultsKey'), getattr(module, 'resultsKey')())

                    # Retrieve results key
                    setattr(self, (processName + 'ErrorsKey'), getattr(module, 'errorsKey')())

                    # Retrieve the pre process variable
                    setattr(self, (processName + 'PreProcess'), getattr(module, 'pre_ProcessVariable')())

                    # If the pre process variable is True
                    # Define the pre process method to call from imported module
                    if getattr(self, processName + 'PreProcess') == True:
                        preMethodToCall = getattr(module, 'pre_' + processName)

                    # Obtain preprocess list
                    if getattr(self, processName + 'PreProcess') == True:
                        preprocessVariable = preMethodToCall(inputFolder, outputFolder)
                    else:
                        preprocessVariable = []

                    # Set kill process boolean to false
                    setattr(self, processName + 'KillBoolean', False)

                    # Define the method to call from imported module
                    methodToCall = getattr(module, processName)

                    # Build list of full file path to each object path
                    if processTest == False:
                        for root, folder, files in os.walk(inputFolder):
                            for filename in files:
                                if filename[-3:] in self.allowedImageFormats:
                                    # Display message when object is found
                                    displayTextVar2.set(('Found object: ' + filename.split('.')[0]))
                                    statusEntry2.update()                            

                                    # Add object to list for processing
                                    objectList.append(os.path.join(root, filename))

                        # Set assigned tasks variable the value of the local object list
                        setattr(self, processName + 'AssignedTasks', objectList)
                    else:
                        # Set up test list of 100
                        objectList = range(100)

                        # Set assigned tasks variable the value of the local object list
                        setattr(self, processName + 'AssignedTasks', objectList)

                    # Set maximum value of progressbar to number of tasks
                    progressBar.config(maximum = len(objectList))
                    progressBar.update()

                    # Set list of actionable widgets for process name
                    setattr(self, processName + 'WidgetList', widgetList)

                    # Set results and error list box instances
                    setattr(self, processName + 'RLB', resultsListBox)
                    setattr(self, processName + 'ELB', errorsListBox)

                    # Set process name progress variables
                    setattr(self, processName + 'Progress', [progressValueVar,
                                                             progressBar])
                    # Set process name display variables
                    setattr(self, processName + 'Display', [displayTextVar1,
                                                             statusEntry1,
                                                             displayTextVar2,
                                                             statusEntry2])
                    
                    # Clear second status message
                    displayTextVar2.set('')
                    statusEntry2.update()                      

                    # Assign tasks to processing thread by sublists of length
                    # determined by number of cpus allocated
                    splitCount = 0
                    processList = getattr(self, processName + 'ProcessList', widgetList)
                    for splitListPart in self._chunkList(objectList, cpusAllocated):
                        
                        for assignmentVariable in splitListPart:
                            
                            # Update display text 1 with assigned task
                            if processTest == False:
                                displayTextVar1.set(('Processing: ' + os.path.basename(assignmentVariable).split('.')[0]))
                            else:
                                displayTextVar1.set(('Processing Test Task: ' + str(assignmentVariable)))

                            # Update first status message
                            statusEntry1.update()

                        # Process function and variable assignment 
                        newProcess = multiprocessing.Process(target = methodToCall, name = processName + str(splitCount),
                                                             args = (splitListPart,
                                                             outputFolder,
                                                             preprocessVariable,
                                                             justLogVar.get(),
                                                             self.resultsQueue))

                        # Append new process to the list
                        processList.append(newProcess)
                        setattr(self, processName + 'ProcessList', processList)

                        # Increment split count by one
                        splitCount += 1

                        # Start the process
                        newProcess.start()

                    # Set results list key entry
                    resultsKeyListBox.insert('end', eval('self.' + str(processName) + 'ResultsKey'))

                    # Set errors list key entry
                    errorsKeyListBox.insert('end', eval('self.' + str(processName) + 'ErrorsKey'))

                    # Update first status entry
                    displayTextVar1.set('')
                    statusEntry1.update()

                    # Update second status entry
                    displayTextVar2.set('All Tasks Assigned.')
                    statusEntry2.update()

                    # Enable kill process button
                    killButton.config(state = Tkinter.NORMAL)
                    killButton.update()

                    break
                elif inputFolder == outputFolder:
                    # Display output folder error
                    self.messageBox(None,
                                    "Output folder cannot be same as input folder.",
                                    'User Entry Error:',
                                    self.messageBoxDictionary['HAND']\
                                    |self.messageBoxDictionary['OK'])            
        else:
            # Display cpu resource error to user
            self.messageBox(None,
                            "User must allocate at least one cpu thread.",
                            'CPU Resource Error:',
                            self.messageBoxDictionary['HAND']\
                            |self.messageBoxDictionary['OK'])

    # Sub Function: Build Menu with default configuration
    def _buildMenu(self, menuFrame):

        # Tab frame name
        tabFrameName = menuFrame.winfo_name()

        # CPU resource label
        CPUSubLabel = Tkinter.Label(menuFrame, text = 'CPU Thread(s):')
        CPUSubLabel.grid(column = 0, row = 0, sticky = Tkinter.E)

        # Processing log label
        processingLogLabel = Tkinter.Label(menuFrame, text = 'Log Only')
        processingLogLabel.grid(column = 1, row = 0, sticky = Tkinter.W)
        
        # Sub Function: Control scroll bar 2 to x view on the key entry
        # and results list
        def multipleCommand(*args, **kwargs):
            if args[0] == 'moveto':
                resultsKeyListBox.xview_moveto(args[1])
                resultsListBox.xview_moveto(args[1])
            elif args[0] == 'scroll':
                resultsKeyListBox.xview_scroll(args[1], args[2])
                resultsListBox.xview_scroll(args[1], args[2])
        # End Sub Function: multipleCommand

        # Sub Function: Reset Menu
        def resetMenu():
            # Reset cpu resource choice combo box
            cpusVar.set('0')
            cpu_Combo_Box.update()

            # Reset log choice combobox
            justLogVar.set('NO')
            log_Combo_Box.update()

            # Clear results key list box
            resultsKeyListBox.delete(0, Tkinter.END)
            resultsKeyListBox.update()

            # Clear results list box
            resultsListBox.delete(0, Tkinter.END)
            resultsListBox.update()

            # Clear error list box
            errorsListBox.delete(0, Tkinter.END)
            errorsListBox.update()

            # Reset first display message entry
            displayText1.set('')
            statusMessage1.update()
            
            # Reset second display message entry
            displayText2.set('')
            statusMessage2.update()

            # Reset progress bar
            progressValueVar.set(0)
            progressBar.update()

            # Disable reset button
            resetButton.config(state = Tkinter.DISABLED)
            resetButton.update()

            # Disable log button
            logButton.config(state = Tkinter.DISABLED)
            logButton.update()

            # Put focus on start button
            startButton.focus()
            startButton.update()

        # Sub Function: Write results to log file
        def generateLog(processName):

            # Get results key
            resultsKey = resultsKeyListBox.get(0)

            # Get errors key
            errorsKey = errorsKeyListBox.get(0)
            
            # Get results from results list box
            resultsList = resultsListBox.get(0, Tkinter.END)

            # Get errors from error list box
            errorsList = errorsListBox.get(0, Tkinter.END)

            # Get folder path from user to save log file
            inputFolder = str(tkFileDialog.askdirectory(parent = menuFrame,
                                                        title = "Please select an input folder for log file."))

            # Create log file name
            logFilePath = os.path.join(inputFolder, (tabFrameName + "_" + time.ctime().replace(' ','_').replace(':','-') + '.txt'))

            # Write start and end process times to log
            with open(logFilePath, 'w+') as logFile:
                logFile.write((tabFrameName + ' time started: ' + (getattr(self, (processName + "TimeStarted"), time.ctime())) + '\n' + '\n'))
                logFile.write((tabFrameName + ' time ended: ' + (getattr(self, (processName + "TimeEnded"), time.ctime())) + '\n' + '\n'))

                # Results
                logFile.write('Results:' + '\n')
                logFile.write((resultsKey + '\n'))
                if len(resultsList) > 0:
                    for lineItem in resultsList:
                        logFile.write((lineItem + '\n'))
                else:
                    logFile.write('There is nothing to log.\n')
                    
                # Errors
                logFile.write('\n' + 'Errors:' + '\n')
                logFile.write((errorsKey + '\n'))
                if len(errorsList) > 0:
                    for lineItem in errorsList:
                        logFile.write((lineItem + '\n'))
                else:
                    logFile.write('There is nothing to log.\n')
                    
        # Start button
        startButton = Tkinter.Button(menuFrame, text = 'Start',
                                     state = Tkinter.NORMAL,
                                     width = 8)
        startButton.grid(column = 0, row = 2, sticky = Tkinter.W)

        # Combo box for cpu resource tracking
        cpusVar = Tkinter.StringVar()
        cpusVar.set('0')
        cpusVarValues = list(xrange(0, self.cpuThreadCount + 1))
        cpu_Combo_Box = ttk.Combobox(menuFrame,
                                     width = 2,
                                     state = 'readonly',
                                     textvariable = cpusVar,
                                     values = cpusVarValues)
        cpu_Combo_Box.grid(column = 0, row = 2, sticky = Tkinter.E)

        # Add cpu resource variable to the main tracker
        self.cpuTrackers.append(cpusVar)

        # Add cpu comboboxes to list
        self.cpuEntries.append(cpu_Combo_Box)

        # Combo box for either running through the process
        # or just logging the results
        justLogVar = Tkinter.StringVar()
        justLogVar.set('NO')
        log_Combo_Box = ttk.Combobox(menuFrame,
                                     width = 3,
                                     state = 'readonly',
                                     textvariable = justLogVar,
                                     values = ['YES', 'NO'])
        log_Combo_Box.grid(column = 1, row = 2, sticky = Tkinter.W)

        # Create list box for results
        resultsListLabel = Tkinter.Label(menuFrame, text = 'Results:')
        resultsListLabel.grid(column = 0, row = 4, sticky = Tkinter.W)
        resultsListBox = Tkinter.Listbox(menuFrame, height = 10, width = 70,
                                         selectmode = Tkinter.EXTENDED,
                                         state = Tkinter.NORMAL)
        resultsListBox.grid(column = 0, columnspan = 2, row = 6,
                            sticky = (Tkinter.W, Tkinter.E))

        # Create vertical scroll bar for results list box
        scrollBarOne = Tkinter.Scrollbar(menuFrame, orient=Tkinter.VERTICAL,
                                         command = resultsListBox.yview)
        scrollBarOne.grid(column = 2, row = 6,
                          sticky = (Tkinter.N, Tkinter.S, Tkinter.W))

        # Create horizontal scroll bar for results list box
        scrollBarTwo = Tkinter.Scrollbar(menuFrame,
                                         orient = Tkinter.HORIZONTAL,
                                         command = multipleCommand)
        scrollBarTwo.grid(column = 0, columnspan = 3, row = 7,
                          sticky = (Tkinter.W, Tkinter.S, Tkinter.E))

        # Set the X and Y scroll commands to the appropriate scroll bars
        resultsListBox['yscrollcommand'] = scrollBarOne.set
        resultsListBox['xscrollcommand'] = scrollBarTwo.set

        # Create list box for results display
        errorsListLabel = Tkinter.Label(menuFrame, text = 'Errors Key:')
        errorsListLabel.grid(column = 0, row = 8, sticky = Tkinter.W)
        errorsListBox = Tkinter.Listbox(menuFrame, height = 5, width = 70,
                                       selectmode = Tkinter.EXTENDED,
                                       state = Tkinter.NORMAL)
        errorsListBox.grid(column = 0, columnspan = 2, row = 10,
                          sticky = (Tkinter.E, Tkinter.W))

        # Create vertical scroll bar for error results list box
        errorScrollVert = Tkinter.Scrollbar(menuFrame,
                                            orient = Tkinter.VERTICAL,
                                            command = errorsListBox.yview)
        errorScrollVert.grid(column = 2, row = 10,
                             sticky = (Tkinter.N, Tkinter.S, Tkinter.W))

        # Create horizontal scroll bar for error results list box
        errorScrollHor = Tkinter.Scrollbar(menuFrame,
                                           orient = Tkinter.HORIZONTAL,
                                           command = errorsListBox.xview)
        errorScrollHor.grid(column = 0, columnspan = 3, row = 11,
                            sticky = (Tkinter.N, Tkinter.W, Tkinter.E))

        # Set the X and Y scroll command to the appropriate scroll bars
        errorsListBox['xscrollcommand'] = errorScrollHor.set
        errorsListBox['yscrollcommand'] = errorScrollVert.set

        # Create readonly entry for displaying result keys
        resultsKeyListBoxLabel = Tkinter.Label(menuFrame, text = 'Results key:')
        resultsKeyListBoxLabel.grid(column = 0, row = 3, sticky = Tkinter.W)
        resultsKeyListBox = Tkinter.Listbox(menuFrame,
                                            height = 1,
                                            width = 70,
                                            selectmode = Tkinter.EXTENDED,
                                            state = Tkinter.NORMAL)
        resultsKeyListBox.grid(column = 0, columnspan = 2, row = 4,
                               sticky = Tkinter.W)
        resultsKeyListBox['xscrollcommand'] = scrollBarTwo.set

        # Create readonly entry for displaying result keys
        errorsKeyListBox = Tkinter.Listbox(menuFrame,
                                           height = 1,
                                           width = 70,
                                           selectmode = Tkinter.EXTENDED,
                                           state = Tkinter.NORMAL)
        errorsKeyListBox.grid(column = 0, columnspan = 2, row = 9,
                               sticky = Tkinter.W)
        errorsKeyListBox['xscrollcommand'] = errorScrollHor.set

        # Create read only entry for displaying program proces updates
        statusLabel = Tkinter.Label(menuFrame, text = 'Status 1:')
        statusLabel.grid(column = 0, row = 14, sticky = Tkinter.W)
        displayText1 = Tkinter.StringVar()
        statusMessage1 = ttk.Entry(menuFrame, width = 30, state = 'readonly',
                                  textvariable = displayText1)
        statusMessage1.grid(column = 0, row = 15, sticky = (Tkinter.W,
                                                            Tkinter.E))

        # Create second read only entry for displaying program progress updates
        statusLabel2 = Tkinter.Label(menuFrame, text = 'Status 2:')
        statusLabel2.grid(column = 1, row = 14, sticky = Tkinter.W)
        displayText2 = Tkinter.StringVar()
        statusMessage2 = ttk.Entry(menuFrame, width = 25, state = 'readonly',
                                   textvariable = displayText2)

        statusMessage2.grid(column = 1, row = 15, sticky = (Tkinter.W,
                                                            Tkinter.E))

        # Create progress bar
        progressLabel = Tkinter.Label(menuFrame, text = "Progress Bar:")
        progressLabel.grid(column = 0, row = 16, sticky = Tkinter.W)
        progressValueVar = Tkinter.IntVar() 
        progressBar = ttk.Progressbar(menuFrame, orient = Tkinter.HORIZONTAL,
                                    length = 130, mode = 'determinate',
                                    variable = progressValueVar)
        progressBar.grid(column = 0, row = 17, sticky = (Tkinter.E, Tkinter.W))

        # Create button for killing menu's processing
        action_with_arg_Kill = functools.partial(self._killProcess,
                                                 tabFrameName)
        killButton = Tkinter.Button(menuFrame, text = 'Kill Process',
                                    state = Tkinter.DISABLED)
        killButton.grid(column = 0, row = 18, sticky = Tkinter.W)
        killButton.config(command = action_with_arg_Kill)

        # Create button for resetting menu
        resetButton = Tkinter.Button(menuFrame, text = 'Reset Menu',
                                     state = Tkinter.DISABLED,
                                     command = resetMenu)
        resetButton.grid(column = 0, row = 19, sticky = Tkinter.W)

        # Create button for logging process errors/results
        action_with_arg_Log = functools.partial(generateLog, tabFrameName)
        logButton = Tkinter.Button(menuFrame, text = 'Create Log',
                                   state = Tkinter.DISABLED,
                                   command = action_with_arg_Log)        
        logButton.grid(column = 1, columnspan = 2, row = 17, sticky = Tkinter.E)        

        # Add arguments to the start button command
        action_with_arg = functools.partial(self._assignProcess,
                                            menuFrame,
                                            tabFrameName,
                                            cpusVar,
                                            justLogVar,
                                            resultsKeyListBox,
                                            errorsKeyListBox,
                                            resultsListBox,
                                            errorsListBox,
                                            killButton,
                                            progressValueVar,
                                            progressBar,
                                            displayText1,
                                            statusMessage1,
                                            displayText2,
                                            statusMessage2,
                                            resetButton,
                                            logButton)
        startButton.config(command = action_with_arg)

        # Update sub menu
        menuFrame.update_idletasks()

    # Class Function: Build main menu that will contain notebook tabs with each
    # individual process
    def _buildMainMenu(self):
        
        # Root
        self.root.title("Multi Menu")
        self.root.resizable(width = Tkinter.FALSE, height = Tkinter.FALSE)

        # Master Frame
        self.masterFrame = Tkinter.Frame(self.root)
        self.masterFrame.grid(column = 0, row = 0, sticky = (Tkinter.N,
                                                             Tkinter.S,
                                                             Tkinter.E,
                                                             Tkinter.W))

        # Configure column weights
        for x in range(18):
            self.masterFrame.columnconfigure(x, weight = 1)

        # Configure row weights
        for x in range(7):
            self.masterFrame.rowconfigure(x, weight = 1)

        # Root protocols

        # When the user presses the red x button quit the program
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        ################################################################################
        # Main menu
        # CPU Count Label
        self.CPUEntryVar = Tkinter.StringVar()
        self.CPUEntryVar.set(('Number of CPUs available for tasking: ['+ str(self.cpuThreadCount)) + ']')
        self.CPUMainEntry = Tkinter.Entry(self.masterFrame, width = 37,
                                     textvariable = self.CPUEntryVar,
                                     state = 'readonly')
        self.CPUMainEntry.grid(column = 0, row = 0, sticky = (Tkinter.N, Tkinter.W))

        # Exit button
        exitButton = Tkinter.Button(self.masterFrame, text = 'Exit Program',
                                    command = self.root.destroy)
        exitButton.grid(column = 0, row = 16, sticky = Tkinter.E)

        # Notebook
        notebook = ttk.Notebook(self.masterFrame, name = 'format')
        notebook.grid(column = 0, row = 2, sticky = (Tkinter.N, Tkinter.S,
                                                     Tkinter.E,
                                                     Tkinter.W))

        # Call tool toplevel menu
        self._callToolMenu(notebook)

        # Lift the main window on top
        if self.toolMenuCanceled == False:
            self.root.attributes('-topmost',True)
            self.root.after_idle(self.root.attributes,'-topmost',False)

            # Enter multi menu loop
            self.masterFrame.mainloop()

################################################################################

# Run GUI in main thread
if __name__ == '__main__':
    MultiMenu()._buildMainMenu()

    # Exit application
    sys.exit()
