import os,sys
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu --single-process'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
tab=sys.argv[1]; sc=int(sys.argv[2]); out=sys.argv[3]; W=int(sys.argv[4]) if len(sys.argv)>4 else 390; H=int(sys.argv[5]) if len(sys.argv)>5 else 844
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(W,H)
l=QEventLoop(); v.loadFinished.connect(lambda ok:l.quit()); v.load(QUrl.fromLocalFile('/workspace/KOVO_PRO_ANALYST_STUDIO.html')); QTimer.singleShot(60000,l.quit); v.show(); l.exec()
def js(c,t=15000):
    b={}; x=QEventLoop(); v.page().runJavaScript(c,0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(t,x.quit); x.exec(); return b.get('v')
def wait(ms):
    x=QEventLoop(); QTimer.singleShot(ms,x.quit); x.exec()
wait(2500)
js("document.querySelector('.tab-btn[data-tab=\"%s\"]').click();"%tab); wait(700)
js("window.scrollTo(0,%d)"%sc); wait(400)
v.grab().save(out); print("saved",out)
