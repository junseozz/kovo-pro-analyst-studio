import os,sys,json,re
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(390,844)
l=QEventLoop(); v.loadFinished.connect(lambda ok:l.quit()); v.load(QUrl.fromLocalFile('/workspace/KOVO_PRO_ANALYST_STUDIO.html')); QTimer.singleShot(60000,l.quit); v.show(); l.exec()
def js(c,t=20000):
    b={}; x=QEventLoop(); v.page().runJavaScript(c,0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(t,x.quit); x.exec(); return b.get('v')
def wait(ms):
    x=QEventLoop(); QTimer.singleShot(ms,x.quit); x.exec()
wait(3500)
js("document.querySelector('.tab-btn[data-tab=\"news\"]').click()"); wait(600)
for k in ["ext","press","notice","kovo"]:
    js("document.querySelector('[data-newskind=\"%s\"]').click()"%k); wait(500)
    print(k, js("document.querySelectorAll('.news-item').length"), js("document.getElementById('screen-news').innerText.replace(/\\n/g,' ').slice(60,220)"))
