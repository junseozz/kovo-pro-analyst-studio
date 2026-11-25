import os,sys
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu --allow-file-access-from-files'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(390,844)
l=QEventLoop(); v.loadFinished.connect(lambda ok:l.quit()); v.load(QUrl.fromLocalFile('/workspace/KOVO_PRO_ANALYST_STUDIO.html')); QTimer.singleShot(60000,l.quit); v.show(); l.exec()
def js(c,t=25000):
    b={}; x=QEventLoop(); v.page().runJavaScript(c,0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(t,x.quit); x.exec(); return b.get('v')
def wait(ms):
    x=QEventLoop(); QTimer.singleShot(ms,x.quit); x.exec()
wait(3000)
for name,url in [("githack","https://raw.githack.com/junseozz/kovo-pro-analyst-studio/main/data/manifest.js"),
                 ("jsdelivr","https://cdn.jsdelivr.net/gh/junseozz/kovo-pro-analyst-studio@main/data/manifest.js")]:
    js("window.__k='wait';window.KOVO_RECEIVE=function(j){window.__k='ok '+(j&&j.checked_at)};var s=document.createElement('script');s.src='%s?t='+Date.now();s.onerror=function(){window.__k='script-error'};document.head.appendChild(s);"%url)
    wait(7000)
    print(name, js("window.__k"))
