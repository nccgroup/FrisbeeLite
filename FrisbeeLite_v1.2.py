# Frisbee Lite 
# by Andy Davis (andy.davis@nccgroup.com)
#
# Frisbee Lite - A USB device fuzzer
#

#!/usr/bin/python
import wx
import usb.core
import usb.util
import sys
import time
import string

USE_GENERIC = 0

if USE_GENERIC:
    from wx.lib.stattext import GenStaticText as StaticText
else:
    StaticText = wx.StaticText
    

class PidVidDialog(wx.Dialog):
    def __init__(
            self, parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition, 
            style=wx.DEFAULT_DIALOG_STYLE,
            useMetal=False,
            ):

        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, size, style)
        self.PostCreate(pre)

        if 'wxMac' in wx.PlatformInfo and useMetal:
            self.SetExtraStyle(wx.DIALOG_EX_METAL)

	self.wPIDListmsb = ["0"]
	self.wPIDListlsb = ["0"]
	self.wVIDListmsb = ["0"]
	self.wVIDListlsb = ["0"]
	self.PID = 0
	self.VID = 0

	self.wPIDListmsb = ["%02x" % i for i in range (256)]
	self.wPIDListlsb = self.wPIDListmsb
	self.wVIDListmsb = self.wPIDListmsb
	self.wVIDListlsb = self.wPIDListmsb

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, -1, "Insert USB device details")
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, "PID:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        
        cbPID1 = wx.ComboBox(self, 600, "0",(0,0),
                         (65, -1), self.wPIDListmsb,
                         wx.CB_DROPDOWN
                         )

	box.Add(cbPID1, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.Bind(wx.EVT_COMBOBOX, self.EvtcbPID1, cbPID1)

	cbPID2 = wx.ComboBox(self, 610, "0",(0,0), 
                         (65, -1), self.wPIDListlsb,
                         wx.CB_DROPDOWN
                         )

	box.Add(cbPID2, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.Bind(wx.EVT_COMBOBOX, self.EvtcbPID2, cbPID2)

        label = wx.StaticText(self, -1, "VID:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        cbVID1 = wx.ComboBox(self, 601, "0",(0,0),
                         (65, -1), self.wVIDListmsb,
                         wx.CB_DROPDOWN
                         )

	box.Add(cbVID1, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbVID1, cbVID1)

	cbVID2 = wx.ComboBox(self, 611, "0",(0,0),
                         (65, -1), self.wVIDListlsb,
                         wx.CB_DROPDOWN
                         )

	box.Add(cbVID2, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbVID2, cbVID2)


        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
                
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def EvtcbPID1(self, event):
        selected = event.GetString()
        self.PID = int (selected,16) << 8

    def EvtcbPID2(self, event):
        selected = event.GetString()
        self.PID += int (selected,16)	

    def EvtcbVID1(self, event):
        selected = event.GetString()
        self.VID = int (selected,16) << 8

    def EvtcbVID2(self, event):
        selected = event.GetString()
        self.VID += int (selected,16)




class MainPanel(wx.Panel):
    def __init__(self, parent, frame=None):
        wx.Panel.__init__(
            self, parent, -1,
            style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE
            )

        self.parent = parent
        self.frame = frame

        self.pid = 0x1297	#iPhone
        self.vid = 0x05ac	#iPhone

	self.dev = 0

        x = 0
        
        self.bmRequestTypeList = []
        self.bRequestList = []
        self.wValueListmsb = []
        self.wValueListlsb = []
        self.wIndexListmsb = [] 
        self.wIndexListlsb = [] 
	self.wLengthListmsb = []
	self.wLengthListlsb = []
 
        self.bmRequestType = 0
        self.bRequest = 0
        self.wValue = 0
        self.wIndex = 0
	self.wLength = 0

        self.bmRequestTypeE = 255
        self.bRequestE = 255
        self.wValueE = 65535
        self.wIndexE = 65535

	self.bmRequestTypefuzz = False
        self.bRequestfuzz = False
        self.wValuefuzz = False
        self.wIndexfuzz = False
        
	self.bmRequestTypeList = ["%02x" % i for i in range (256)]
        
        self.bRequestList = self.bmRequestTypeList
        self.wValueListmsb = self.bmRequestTypeList
	self.wValueListlsb = self.bmRequestTypeList
	self.wIndexListmsb = self.bmRequestTypeList
	self.wIndexListlsb = self.bmRequestTypeList
	self.wLengthListmsb = self.bmRequestTypeList
	self.wLengthListlsb = self.bmRequestTypeList	
                           
        self.fuzzing = 0
 
        self.SetBackgroundColour("White")
        self.Refresh()
        
# create IDs   
     
        self.ID_Select_Device = wx.NewId()
        self.ID_About = wx.NewId()
             
# create menu
        
        self.mb = wx.MenuBar()

        device_menu = wx.Menu()
        device_menu.Append(self.ID_Select_Device, "&Select USB device")
        device_menu.Append(self.ID_About, "&About")       

        device_menu.AppendSeparator()
        device_menu.Append(wx.ID_EXIT, "Exit")

        self.mb.Append(device_menu, "File")
        self.parent.SetMenuBar(self.mb)
                
# Create status bar

        self.statusbar = self.parent.CreateStatusBar(3, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-1,-2, -2])
        self.statusbar.SetStatusText("", 0)
        self.statusbar.SetStatusText("Connection Status: Not connected", 1) 
        self.statusbar.SetStatusText("Fuzzing Status: Not fuzzing", 2)                
        
# Background images        
        
        image_file = 'images/frisbee_logo.png'
        image = wx.Bitmap(image_file)
        image_size = image.GetSize()
        bm = wx.StaticBitmap(self, wx.ID_ANY, image, size=image_size, pos=(0,3))
        
        image_file = 'images/frisbee_name.png'
        image = wx.Bitmap(image_file)
        image_size = image.GetSize()
        bm = wx.StaticBitmap(self, wx.ID_ANY, image, size=image_size, pos=(195,75))

        image_file = 'images/nccgrouplogo.png'
        image = wx.Bitmap(image_file)
        image_size = image.GetSize()
        bm = wx.StaticBitmap(self, wx.ID_ANY, image, size=image_size, pos=(310,10))

# Titles

        text = wx.StaticText(self, -1, "Start values",pos=(120,130))
        text.SetBackgroundColour('White')
        font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)

        text = wx.StaticText(self, -1, "Fuzz?",pos=(252,130))
        text.SetBackgroundColour('White')
        font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)

        text = wx.StaticText(self, -1, "End values",pos=(290,130))
        text.SetBackgroundColour('White')
        font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)

# Combo boxes

        text = wx.StaticText(self, -1, "bmRequestType:  ",pos=(10,150))
        text.SetBackgroundColour('White')
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)
        
        self.cbmRequestType = wx.ComboBox(self, 500, "00", (120, 150),
                         (130, -1), self.bmRequestTypeList,
                         wx.CB_DROPDOWN
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbmRequestType, self.cbmRequestType)
        
        text = wx.StaticText(self, -1, "bRequest:  ",pos=(10,180))
        text.SetBackgroundColour('White')
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)
        
        self.cbRequest = wx.ComboBox(self, 501, "00", (120, 180),
                         (130, -1), self.bRequestList,
                         wx.CB_DROPDOWN
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbRequest, self.cbRequest)


        text = wx.StaticText(self, -1, "wValue:  ",pos=(10,210))
        text.SetBackgroundColour('White')
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)
        
        self.cbValue1 = wx.ComboBox(self, 502, "00", (120, 210),
                         (65, -1), self.wValueListmsb,
                         wx.CB_DROPDOWN
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbValue1, self.cbValue1)

	self.cbValue2 = wx.ComboBox(self, 512, "00", (185, 210),
                         (65, -1), self.wValueListlsb,
                         wx.CB_DROPDOWN
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbValue2, self.cbValue2)

        text = wx.StaticText(self, -1, "wIndex:  ",pos=(10,240))
        text.SetBackgroundColour('White')
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)
        
        self.cbIndex1 = wx.ComboBox(self, 503, "00", (120, 240),
                         (65, -1), self.wIndexListmsb,
                         wx.CB_DROPDOWN
                         )               
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbIndex1, self.cbIndex1)

        self.cbIndex2 = wx.ComboBox(self, 513, "00", (185, 240),
                         (65, -1), self.wIndexListlsb,
                         wx.CB_DROPDOWN
                         )               
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbIndex2, self.cbIndex2)
    
        self.cbmRequestTypeE = wx.ComboBox(self, 504, "ff", (290, 150),
                         (130, -1), self.bmRequestTypeList,
                         wx.CB_DROPDOWN
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbmRequestTypeE, self.cbmRequestTypeE)
             
        
        self.cbRequestE = wx.ComboBox(self, 505, "ff", (290, 180),
                         (130, -1), self.bRequestList,
                         wx.CB_DROPDOWN
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbRequestE, self.cbRequestE)
          
        self.cbValue1E = wx.ComboBox(self, 506, "ff", (290, 210),
                         (65, -1), self.wValueListmsb,
                         wx.CB_DROPDOWN
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbValue1E, self.cbValue1E)

	self.cbValue2E = wx.ComboBox(self, 516, "ff", (355, 210),
                         (65, -1), self.wValueListlsb,
                         wx.CB_DROPDOWN
                         )
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbValue2E, self.cbValue2E)
              
        self.cbIndex1E = wx.ComboBox(self, 507, "ff", (290, 240),
                         (65, -1), self.wIndexListmsb,
                         wx.CB_DROPDOWN
                         )               
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbIndex1E, self.cbIndex1E)

        self.cbIndex2E = wx.ComboBox(self, 517, "ff", (355, 240),
                         (65, -1), self.wIndexListlsb,
                         wx.CB_DROPDOWN
                         )               
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbIndex2E, self.cbIndex2E)


        text = wx.StaticText(self, -1, "wLength:  ",pos=(10,270))
        text.SetBackgroundColour('White')
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)
        
        self.cbLength1 = wx.ComboBox(self, 508, "00", (120, 270),
                         (65, -1), self.wLengthListmsb,
                         wx.CB_DROPDOWN
                         )               
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbLength1, self.cbLength1)

        self.cbLength2 = wx.ComboBox(self, 518, "00", (185, 270),
                         (65, -1), self.wLengthListlsb,
                         wx.CB_DROPDOWN
                         )               
        self.Bind(wx.EVT_COMBOBOX, self.EvtcbLength2, self.cbLength2)

        
# Checkboxes

	cb1 = wx.CheckBox(self, -1, "", (260, 150), (20, 20), wx.BORDER)  
	self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox1, cb1)

	cb2 = wx.CheckBox(self, -1, "", (260, 180), (20, 20), wx.BORDER) 
	self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox2, cb2)

	cb3 = wx.CheckBox(self, -1, "", (260, 210), (20, 20), wx.BORDER) 
	self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox3, cb3)

	cb4 = wx.CheckBox(self, -1, "", (260, 240), (20, 20), wx.BORDER)   
	self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox4, cb4)       

# Buttons

        imgStart = wx.Image('images/play.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        bmbSingleShot = wx.BitmapButton(self, -1, imgStart, (10, 325), style = wx.NO_BORDER) 

        imgStart = wx.Image('images/play.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        bmbStart = wx.BitmapButton(self, -1, imgStart, (90, 325), style = wx.NO_BORDER)             
        
        imgStop = wx.Image('images/stop.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        bmbStop = wx.BitmapButton(self, -1, imgStop, (140, 325), style = wx.NO_BORDER)   
   
        txt = wx.StaticText(self, -1, "Progress:  ",pos=(220,300))  
        txt.SetBackgroundColour('White')      
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        txt.SetFont(font) 
        
# Progress gauge        
        
        self.FuzzProgress = wx.Gauge(self, -1, 256, (220, 325), (200, 30))
        
# Text output pane

        text = StaticText(self, -1, "Fuzzer controls:", (82, 300))
        text.SetBackgroundColour('White')
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)
        
        text = StaticText(self, -1, "Single:", (10, 300))
        text.SetBackgroundColour('White')
        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)        

# Bind events

        self.parent.Bind(wx.EVT_MENU, self.SelectDevice, id=self.ID_Select_Device)
        self.parent.Bind(wx.EVT_MENU, self.About, id=self.ID_About)
        self.parent.Bind(wx.EVT_MENU, self.CloseMe, id=wx.ID_EXIT)     
        
        self.Bind(wx.EVT_BUTTON, self.SingleShot, bmbSingleShot)
        self.Bind(wx.EVT_BUTTON, self.FuzzDevice, bmbStart) 
        self.Bind(wx.EVT_BUTTON, self.StopFuzzing, bmbStop)   
           
 # methods

    def	updatevalues(self):

	if self.bmRequestType == 256:
		self.bmRequestType = 255
	if self.bRequest == 256:
		self.bRequest = 255
	if self.wValue == 65536:
		self.wValue = 65535
	if self.wIndex == 65536:
		self.wIndex = 65535

	self.cbmRequestType.SetValue("%02x" % self.bmRequestType)
	self.cbRequest.SetValue("%02x" % self.bRequest)

	msb = self.wValue
	self.cbValue1.SetValue("%02x" % (msb >> 8))
	lsb = self.wValue
	self.cbValue2.SetValue("%02x" % (lsb & 0xff))


	msb = self.wIndex
	self.cbIndex1.SetValue("%02x" % (msb >> 8))
	lsb = self.wIndex
	self.cbIndex2.SetValue("%02x" % (lsb & 0xff))

    def EvtcbmRequestType(self, event):
        selected = event.GetString()
        self.bmRequestType = int (selected,16)	

    def EvtcbRequest(self, event):
        selected = event.GetString()
        self.bRequest = int (selected,16)	
    
    def EvtcbValue1(self, event):
        selected = event.GetString()
	lsb = self.wValue & 0xff
        self.wValue = int (selected,16) << 8 
	self.wValue += lsb	

    def EvtcbValue2(self, event):
        selected = event.GetString()
	msb = self.wValue & 0xff00
        self.wValue = int (selected,16)
	self.wValue += msb	

    def EvtcbIndex1(self, event):
        selected = event.GetString()
	lsb = self.wIndex & 0xff
        self.wIndex = int (selected,16)	<< 8
	self.wIndex += lsb

    def EvtcbIndex2(self, event):
        selected = event.GetString()
	msb = self.wIndex & 0xff00
        self.wIndex = int (selected,16)
	self.wIndex += msb

    def EvtcbLength1(self, event):
        selected = event.GetString()
	lsb = self.wLength & 0xff
        self.wLength = int (selected,16) << 8
	self.wLength += lsb

    def EvtcbLength2(self, event):
        selected = event.GetString()
	msb = self.wLength & 0xff00
        self.wLength = int (selected,16)
	self.wLength += msb

    def EvtcbmRequestTypeE(self, event):
        selected = event.GetString()
        self.bmRequestTypeE = int (selected,16)	

    def EvtcbRequestE(self, event):
        selected = event.GetString()
        self.bRequestE = int (selected,16)
    
    def EvtcbValue1E(self, event):
        selected = event.GetString()
	lsb = self.wValueE & 0xff
        self.wValueE = int (selected,16) << 8
	self.wValueE += lsb

    def EvtcbValue2E(self, event):
        selected = event.GetString()
	msb = self.wValueE & 0xff00
        self.wValueE = int (selected,16)	
	self.wValueE += msb

    def EvtcbIndex1E(self, event):
        selected = event.GetString()
	lsb = self.wIndexE & 0xff
        self.wIndexE = int (selected,16) << 8
	self.wIndexE += lsb

    def EvtcbIndex2E(self, event):
        selected = event.GetString()
	msb = self.wIndexE & 0xff00
        self.wIndexE = int (selected,16)
	self.wIndexE += msb

    def EvtCheckBox1(self, event):
        self.bmRequestTypefuzz = event.IsChecked()
	
    def EvtCheckBox2(self, event):
        self.bRequestfuzz = event.IsChecked()

    def EvtCheckBox3(self, event):
        self.wValuefuzz = event.IsChecked()

    def EvtCheckBox4(self, event):
        self.wIndexfuzz = event.IsChecked()

    def SelectDevice(self, event):
        useMetal = False
        if 'wxMac' in wx.PlatformInfo:
            useMetal = self.cb.IsChecked()
            
        dlg = PidVidDialog(self, -1, "Select Device", size=(350, 200),
                         #style=wx.CAPTION | wx.SYSTEM_MENU | wx.THICK_FRAME,
                         style=wx.DEFAULT_DIALOG_STYLE, # & ~wx.CLOSE_BOX,
                         useMetal=useMetal,
                         )
        dlg.CenterOnScreen()
        
        val = dlg.ShowModal()
	if val == wx.ID_OK:

		self.dev = usb.core.find(idVendor=dlg.VID, idProduct=dlg.PID)
 
        	if self.dev is None:
	  		self.statusbar.SetStatusText("Connection Status: Not connected", 1)
          		wx.MessageBox("Device not found!", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)	  
          		return(1)
		else: 

			self.statusbar.SetStatusText("Connection Status: Connected", 1)
          		wx.MessageBox("Connected to device", caption="Success", style=wx.OK|wx.ICON_INFORMATION, parent=self)	  
          		return(1)
			self.vid = dlg.VID
			self.pid = dlg.PID
   
        dlg.Destroy()



    def SingleShot(self, event):
 
	if not self.dev:
          self.dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)

        if self.dev is None:
          wx.MessageBox("Device not found!", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
          return(1) 
  
	self.dev.set_configuration()     

	try:
	
          print time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()),
          print "    bmRequestType: " + "%02x" % self.bmRequestType + " bRequest: " + "%02x" % self.bRequest + " wValue: " + "%04x" % self.wValue + " wIndex: " + "%04x" % self.wIndex + " wLength: " + "%04x" % self.wLength
       	  
          recv = self.dev.ctrl_transfer(self.bmRequestType, self.bRequest, self.wValue, self.wIndex, self.wLength)
	  print "Received: " + str(recv)
	  print "Received: " + recv [0]
	  print "Received: " + recv [0] [0]

	except:
	  pass


    def FuzzDevice(self, event):

	logfilepath = "FrisbeeLite_logfile_" + time.strftime("%Y-%m-%d", time.localtime()) + ".txt"
	fplog = file(logfilepath, 'a')	
	fplog.write("\n\n**** FrisbeeLite - Log file ****\n\n")
	fplog.close()

	firstrun = True
        self.fuzzing = 1
	self.statusbar.SetStatusText("Fuzzing Status: Fuzzing", 2) 

	if not self.dev:
          self.dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
 
        if self.dev is None:
	  self.statusbar.SetStatusText("Fuzzing Status: Not fuzzing", 2)
          wx.MessageBox("Device not found!", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)	  
          return(1) 
 
	self.dev.set_configuration()

	if (self.bmRequestTypefuzz and not firstrun): 
	  self.bmRequestType = 0
	while (self.bmRequestType < self.bmRequestTypeE+1):
          self.FuzzProgress.SetValue(self.bmRequestType+1)
	  
	  if (self.bRequestfuzz and not firstrun): 
	    self.bRequest = 0
          while (self.bRequest < self.bRequestE+1):
     	    
	    if (self.wValuefuzz and not firstrun):
	      self.wValue = 0
     	    while (self.wValue < self.wValueE+1):
	      
	      if (self.wIndexfuzz and not firstrun):
	        self.wIndex = 0
              while (self.wIndex < self.wIndexE+1):
                wx.Yield() 
		            
                if (self.fuzzing == 1):
		  firstrun = False

		  try:  

		    fplog = file(logfilepath, 'a')	
		    fplog.write(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
		    line = "    bmRequestType: " + "%02x" % self.bmRequestType + " bRequest: " + "%02x" % self.bRequest + " wValue: " + "%04x" % self.wValue + " wIndex: " + "%04x" % self.wIndex + " wLength: " + "%04x" % self.wLength
		    fplog.write(line)
	            fplog.write("\n")	
		    fplog.close()                
                    
                    print time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()),
                    print "    bmRequestType: " + "%02x" % self.bmRequestType + " bRequest: " + "%02x" % self.bRequest + " wValue: " + "%04x" % self.wValue + " wIndex: " + "%04x" % self.wIndex + " wLength: " + "%04x" % self.wLength
		  
		    recv = self.dev.ctrl_transfer(self.bmRequestType, self.bRequest, self.wValue, self.wIndex, self.wLength)
		    print "Received: " + repr(recv)

		    fplog = file(logfilepath, 'a')
		    line = "Received: " + repr(recv)
		    fplog.write(line)
		    fplog.write("\n")
		    fplog.close()

                  except:

                    pass
                
                else:
	          self.fuzzing = 0
		  self.statusbar.SetStatusText("Fuzzing Status: Not fuzzing", 2)
		  self.FuzzProgress.SetValue(0)
		  self.updatevalues()
                  return

                if (self.wIndexfuzz):
                  self.wIndex +=1
	        else:
                  break
  
              if (self.wValuefuzz):    
                self.wValue +=1
              else:
                break
           
            if (self.bRequestfuzz):  
              self.bRequest +=1
            else:
              break 
          if (self.bmRequestTypefuzz):  
            self.bmRequestType +=1
	  else:
 	    break

	self.fuzzing = 0
	self.statusbar.SetStatusText("Fuzzing Status: Not fuzzing", 2)
	self.FuzzProgress.SetValue(0)
	self.updatevalues()
	return
    
    def StopFuzzing(self, event):
        self.fuzzing = 0
	self.statusbar.SetStatusText("Fuzzing Status: Not fuzzing", 2)
        return
        
    def UpdateText(self):
        text = StaticText(self, -1, self.sent, (20, 430))
        text.SetBackgroundColour('White')
        font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL)
        text.SetFont(font)

        return(0)
    
    def About(self, event):
        wx.MessageBox("Frisbee Lite v1.2: Andy Davis, NGS Secure 2012", caption="Information", style=wx.OK|wx.ICON_INFORMATION, parent=self)
        return(1)
        
    def CloseMe(self, event):
        self.parent.Close(True)


app = wx.App(False)  
frame = wx.Frame(None, wx.ID_ANY, "Frisbee Lite", size=(450,440)) 

win = MainPanel(frame)
frame.Show(True)    
app.MainLoop()
