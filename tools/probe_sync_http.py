import os,sys,threading,http.server,socketserver,functools
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin','*'); super().end_headers()
    def log_message(self,*a): pass
class S(socketserver.ThreadingTCPServer): allow_reuse_address=True
srv=S(('127.0.0.1',8799), functools.partial(H, directory='/workspace'))
threading.Thread(target=srv.serve_forever, daemon=True).start()
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(390,844)
l=QEventLoop(); v.loadFinished.connect(lambda ok:l.quit()); v.load(QUrl('http://127.0.0.1:8799/KOVO_PRO_ANALYST_STUDIO.html')); QTimer.singleShot(60000,l.quit); v.show(); l.exec()
def js(c,t=30000):
    b={}; x=QEventLoop(); v.page().runJavaScript(c,0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(t,x.quit); x.exec(); return b.get('v')
def wait(ms):
    x=QEventLoop(); QTimer.singleShot(ms,x.quit); x.exec()
wait(4000)
print("STATUS0", js("document.getElementById('sync-status').textContent"))
js("window.__s='';KOVO_APP.syncOnce(true).then(r=>{window.__s=JSON.stringify(r).slice(0,200)}).catch(e=>{window.__s='ERR '+e});")
wait(25000)
print("SYNC", js("window.__s"))
print("STATUS", js("document.getElementById('sync-status').textContent"))
print("CHECKED", js("localStorage.getItem('kovo_sync_checked_at')"))
print("NEWSCHECK", js("(function(){var s=document.querySelector('.tab-btn[data-tab=\"news\"]');s.click();return document.getElementById('news-checked').textContent;})()"))
srv.shutdown()
