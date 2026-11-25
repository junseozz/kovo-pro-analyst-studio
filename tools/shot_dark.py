import os,sys
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu --single-process'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(int(sys.argv[2]),int(sys.argv[3]))
l=QEventLoop(); v.loadFinished.connect(lambda ok:l.quit()); v.load(QUrl.fromLocalFile('/workspace/KOVO_PRO_ANALYST_STUDIO.html')); QTimer.singleShot(60000,l.quit); v.show(); l.exec()
def js(c,t=15000):
    b={}; x=QEventLoop(); v.page().runJavaScript(c,0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(t,x.quit); x.exec(); return b.get('v')
def wait(ms):
    x=QEventLoop(); QTimer.singleShot(ms,x.quit); x.exec()
wait(2500)
js("document.documentElement.setAttribute('data-theme','dark'); if(window.KOVO_APP)KOVO_APP.render();"); wait(500)
js("document.querySelector('.tab-btn[data-tab=\"%s\"]').click();"%sys.argv[1]); wait(600)
v.grab().save(sys.argv[4]); print("saved")
