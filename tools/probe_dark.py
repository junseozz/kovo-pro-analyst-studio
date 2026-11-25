import os,sys
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu --single-process'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(390,844)
l=QEventLoop(); v.loadFinished.connect(lambda ok:l.quit()); v.load(QUrl.fromLocalFile('/workspace/KOVO_PRO_ANALYST_STUDIO.html')); QTimer.singleShot(60000,l.quit); v.show(); l.exec()
def js(c,t=15000):
    b={}; x=QEventLoop(); v.page().runJavaScript(c,0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(t,x.quit); x.exec(); return b.get('v')
def wait(ms):
    x=QEventLoop(); QTimer.singleShot(ms,x.quit); x.exec()
wait(4000)
print("imgs light", js("(function(){var a=document.querySelectorAll('img');var ok=0;for(var i=0;i<a.length;i++){if(a[i].complete&&a[i].naturalWidth>0)ok++;}return ok+'/'+a.length;})()"))
js("document.documentElement.setAttribute('data-theme','dark')"); wait(3500)
print("imgs dark", js("(function(){var a=document.querySelectorAll('img');var ok=0;for(var i=0;i<a.length;i++){if(a[i].complete&&a[i].naturalWidth>0)ok++;}return ok+'/'+a.length;})()"))
print("btn rect", js("(function(){var b=document.querySelector('.league-btn.active');var r=b.getBoundingClientRect();return JSON.stringify([r.x,r.y,r.width,r.height]);})()"))
print("btn color", js("(function(){var b=document.querySelector('.league-btn.active');var c=getComputedStyle(b);return c.color+'/'+c.backgroundColor+'/'+c.visibility+'/'+c.opacity;})()"))
v.grab().save('/workspace/work_tmp/kovo_v1/verify/dark_probe.png')
