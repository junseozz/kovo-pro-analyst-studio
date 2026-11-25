import os,sys,json
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(390,844)
l=QEventLoop(); v.loadFinished.connect(lambda ok:l.quit()); v.load(QUrl.fromLocalFile('/workspace/KOVO_PRO_ANALYST_STUDIO.html')); QTimer.singleShot(90000,l.quit); v.show(); l.exec()
def js(c,t=25000):
    b={}; x=QEventLoop(); v.page().runJavaScript(c,0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(t,x.quit); x.exec(); return b.get('v')
def wait(ms):
    x=QEventLoop(); QTimer.singleShot(ms,x.quit); x.exec()
wait(3000)
js("window.__r='';fetch('https://raw.githubusercontent.com/junseozz/kovo-pro-analyst-studio/main/data/manifest.json',{cache:'no-store'}).then(r=>r.text()).then(t=>{window.__r='ok '+t.length}).catch(e=>{window.__r='err '+e});")
wait(6000)
print("FETCH", js("window.__r"))
js("window.__s='';KOVO_APP.syncOnce(true).then(r=>{window.__s=JSON.stringify(r)}).catch(e=>{window.__s='ERR '+e});")
wait(20000)
print("SYNC", js("window.__s"))
print("STATUS", js("document.getElementById('sync-status').textContent"))
print("CHECKED", js("localStorage.getItem('kovo_sync_checked_at')"))
print("KDGEN", js("KOVO_APP.KD.gen"))
