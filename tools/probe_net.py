import os,sys
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(400,300)
l=QEventLoop()
def fin(ok): print("LOAD",ok,flush=True); l.quit()
v.loadFinished.connect(fin); v.load(QUrl('https://raw.githack.com/junseozz/kovo-pro-analyst-studio/main/data/manifest.json')); QTimer.singleShot(40000,l.quit); v.show(); l.exec()
b={}; x=QEventLoop(); v.page().runJavaScript("document.body?document.body.innerText.slice(0,120):'no'",0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(8000,x.quit); x.exec()
print("BODY", b.get('v'), flush=True)
