# -*- coding: UTF-8 -*-  
import time
import re
import wmi
from threading import Thread
import thread
import wx
from Exscript import Account
from Exscript.protocols import SSH2
from ping import Ping




class Router():
    __conn = SSH2()
    
    def __init__(self,ip,username='admin',password='admin',enablepassword='admin',):
        self.ip = ip
        self.username = username
        self.password = password
        self.enablepassword = enablepassword
        self.ssh_connect()
    
    def ssh_connect(self):
        account = Account(self.username,self.password)
        self.__conn.connect(self.ip)
        self.__conn.login(account)
        return self.__conn
    
    def enable(self):
        self.__conn.send('en\n')
        self.__conn.expect('password:')
        self.__conn.execute(self.enablepassword)
        return self.__conn
    
    def close(self,Type=True):
        self.__conn.close(Type)

class ShowSignalThread(Thread):
    
    def __init__(self,windows):
        Thread.__init__(self)
        self.breakFlag = False
        self.windows = windows
        self.router_ip = self.get_gateway()
        for ip in self.router_ip:
            try:
                self.router = Router(ip)
                self.windows.sendMessage(ip+u'路由器登陆成功')
                self.encmd = self.router.enable()
                self.windows.sendMessage(u'enable模式登陆成功')
                self.start()
            except:
                self.windows.sendMessage(ip+u'路由器登陆失败')
            else:
                break
            
     
    def get_gateway(self):
        
            #pythoncom.CoInitialize()
            wmi_obj = wmi.WMI()
            wmi_sql = "select DefaultIPGateway from Win32_NetworkAdapterConfiguration where IPEnabled=TRUE"
            wmi_out = wmi_obj.query( wmi_sql )
            ip=[]
            for dev in wmi_out:
                if dev:
                    try:
                        temp = dev.DefaultIPGateway[0]
                    except TypeError:
                        self.windows.sendMessage(u'网关地址获取失败')
                        self.windows.sendMessage(u'1、请检查网线是否插好并且连通')
                        self.windows.sendMessage(u'2、请检查网本机网络参数设置是否正确')
                    else:
                        ip.append(temp)
                        self.windows.sendMessage(u'获取网关地址成功！地址为：'+temp)
            
            return ip 
            
        
        
            

    def show_signal(self,type):
        
        cmd=None
        
        if type ==1:    #电信
            cmd = 'sh cellular 1/0 radio'
        elif type ==3:  #联通
            cmd = 'sh cellular 3/0 radio'
        if cmd!=None and self.encmd!=None:
        
            self.encmd.execute(cmd)
            text = self.encmd.response
            t = re.search('(?<=Indicate: )\d+',text,re.M|re.I)
            signal = t.group()
            
            if type ==1:
                wx.CallAfter(self.windows.UpdateSignal1,str(signal))
            elif type ==3:
                wx.CallAfter(self.windows.UpdateSignal2,str(signal))
    def stop(self):
        self.breakFlag = True
    
    def run(self):
        while True:
            if self.breakFlag:
                break
            self.show_signal(1)
            self.show_signal(3)
            time.sleep(3)
        self.router.close()
    
class MyFrame1(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title= u'3G信号检测工具',size=(500,500))
        
        self.thread=None
        self.p = None
        
        panel = wx.Panel(self)
        self.left = wx.BoxSizer(wx.VERTICAL)
        self.right = wx.BoxSizer(wx.VERTICAL)
        
        self.startBtn = wx.Button(panel, -1, u"开始")
        self.stopBtn = wx.Button(panel, -1, u"停止")
        self.pingBtn = wx.Button(panel,-1,u"Ping生产服务器")
        self.stopPingBtn = wx.Button(panel,-1,u"停止Ping生产服务器")
        
        self.log = wx.TextCtrl(panel,-1,"",style=wx.TE_RICH|wx.TE_MULTILINE)
        
        self.signal1 = wx.Gauge(panel,-1,range=31,size=(100,20),style = wx.GA_HORIZONTAL)
        self.signal1.SetBezelFace(3)
        self.signal1.SetShadowWidth(3)
        self.signal2 = wx.Gauge(panel,-1,range=31,size=(100,20),style = wx.GA_HORIZONTAL)
        self.signal2.SetBezelFace(3)
        self.signal2.SetShadowWidth(3) 
 
        self.tc1 = wx.StaticText(panel, -1, u"电信3G信号强度:        ")
        self.tc2 = wx.StaticText(panel, -1, u"联通3G信号强度:        ")
        
        self.tc3 = wx.StaticText(panel, -1, u"与服务器通信平均延迟")
        
        self.menu = wx.BoxSizer(wx.VERTICAL)
        self.menu.Add(self.startBtn,0,wx.RIGHT,15)
        self.menu.Add(self.stopBtn,0,wx.RIGHT,15)
        self.right.Add(self.pingBtn,0,wx.RIGHT,15)
        self.right.Add(self.stopPingBtn,0,wx.RIGHT,15)
        self.right.Add(self.tc3,0,wx.RIGHT,15)
        
        self.left.Add(self.tc1,0,wx.LEFT,15)
        self.left.Add(self.signal1,0,wx.LEFT,15)
        self.left.Add(self.tc2,0,wx.LEFT,15)
        self.left.Add(self.signal2,0,wx.LEFT,15)
        
        self.top = wx.BoxSizer(wx.HORIZONTAL)
        self.top.Add(self.menu,0,wx.LEFT|wx.EXPAND, 5)
        self.top.Add(self.left,0,wx.LEFT|wx.EXPAND, 5)
        self.top.Add(self.right,0,wx.LEFT|wx.EXPAND, 5)
        
        self.main = wx.BoxSizer(wx.VERTICAL)
        self.main.Add(self.top,0,wx.ALL|wx.EXPAND,5)
        self.main.Add(self.log,1,wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(self.main)
        
        self.Bind(wx.EVT_CLOSE,  self.OnCloseWindow)
        self.Bind(wx.EVT_BUTTON, self.OnStartBtn,self.startBtn)
        self.Bind(wx.EVT_BUTTON, self.OnStopBtn,self.stopBtn)
        self.Bind(wx.EVT_BUTTON, self.pingServer, self.pingBtn)
        self.Bind(wx.EVT_BUTTON, self.stopPingServer, self.stopPingBtn)
    
    def OnCloseWindow(self, evt):
        self.Destroy()
    
    def OnStartBtn(self,evt):
        self.thread = ShowSignalThread(self)
        self.startBtn.Disable()
        #except TypeError:
            #self.
            
    def OnStopBtn(self,evt):
        if self.thread!=None:
            self.thread.stop()
            self.thread = None
        self.startBtn.Enable()
        self.UpdateSignal1('0')
        self.UpdateSignal2('0')
        
    def UpdateSignal1(self,msg):
        self.signal1.SetValue(int(msg))
        self.SetTc1(msg)
    
    def UpdateSignal2(self,msg):
        self.signal2.SetValue(int(msg))
        self.SetTc2(msg)
        
    def SetTc1(self,msg):
        percent = int(msg)*100/31
        self.tc1.SetLabel(u'电信3G信号强度:'+str(percent)+'%')
    
    def SetTc2(self,msg):
        percent = int(msg)*100/31
        self.tc2.SetLabel(u'联通3G信号强度:'+str(percent)+'%')
    
    def sendMessage(self, msg):
        self.log.AppendText(msg+"\n")
    
    def verbose_ping(self,hostname, timeout=1000, count=3, packet_size=55):
        self.p = Ping(hostname, timeout, packet_size,windows=self)
        self.p.run(count)
    
    def pingServer(self,evt):
        thread.start_new(self.verbose_ping, ("192.168.1.1", 4000,500,32))
    
    def stopPingServer(self,evt):
        self.p.stopRun()
    
    def showPing(self,msg):
        self.tc3.SetLabelText(u"与服务器通信平均延迟%0.3fms"%(msg))
    
if __name__=="__main__":
    app = wx.PySimpleApp()
    frame = MyFrame1()
    frame.Show()
    app.MainLoop()