import os,sys
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(390,844)
l=QEventLoop(); v.loadFinished.connect(lambda ok:l.quit()); v.load(QUrl.fromLocalFile('/workspace/KOVO_PRO_ANALYST_STUDIO.html')); QTimer.singleShot(60000,l.quit); v.show(); l.exec()
def js(c,t=15000):
    b={}; x=QEventLoop(); v.page().runJavaScript(c,0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(t,x.quit); x.exec(); return b.get('v')
def wait(ms):
    x=QEventLoop(); QTimer.singleShot(ms,x.quit); x.exec()
wait(2500)
tests=[("vue-cdn","https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.js"),
       ("gh-raw-js","https://raw.githubusercontent.com/junseozz/kovo-pro-analyst-studio/main/data/manifest.js"),
       ("jsdelivr-nq","https://cdn.jsdelivr.net/gh/junseozz/kovo-pro-analyst-studio/main/data/manifest.js"),
       ("githack-nq","https://raw.githack.com/junseozz/kovo-pro-analyst-studio/main/data/manifest.js")]
for name,url in tests:
    js("window.__k='wait';var s=document.createElement('script');s.src='%s';s.onload=function(){window.__k='loaded'};s.onerror=function(){window.__k='error'};document.head.appendChild(s);"%url)
    wait(6000); print(name, js("window.__k"), js("typeof window.KOVO_RECEIVE"))
