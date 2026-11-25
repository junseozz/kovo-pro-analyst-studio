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
wait(3000)
print(js("(function(){var b=document.querySelector('.league-btn.active');var c=getComputedStyle(b);return c.color+' | '+c.backgroundColor+' | '+b.outerHTML.slice(0,80);})()"))
js("document.documentElement.setAttribute('data-theme','dark')"); wait(300)
print(js("(function(){var b=document.querySelector('.league-btn.active');var c=getComputedStyle(b);return c.color+' | '+c.backgroundColor;})()"))
print(js("(function(){var s=document.styleSheets[0];var out=[];for(var i=0;i<s.cssRules.length;i++){var r=s.cssRules[i];if(r.cssText&&r.cssText.indexOf('league-btn')>=0)out.push(r.cssText.slice(0,120));}return out.join(' || ');})()"))
