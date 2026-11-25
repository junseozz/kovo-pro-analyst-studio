import os,sys,json
os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['QT_OPENGL']='software'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS']='--no-sandbox --disable-gpu'
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl,QTimer,QEventLoop
chunk=json.load(open('/workspace/work_tmp/kovo_v1/repo/data/core.json',encoding='utf-8'))
chunk['std']['023']['M'][0][2]='연동테스트팀'
chunk['gen']='2026-11-25T23:00:00+09:00'
app=QApplication(sys.argv[:1]); v=QWebEngineView(); v.resize(390,844)
l=QEventLoop(); v.loadFinished.connect(lambda ok:l.quit()); v.load(QUrl.fromLocalFile('/workspace/KOVO_PRO_ANALYST_STUDIO.html')); QTimer.singleShot(60000,l.quit); v.show(); l.exec()
def js(c,t=30000):
    b={}; x=QEventLoop(); v.page().runJavaScript(c,0,lambda r:(b.__setitem__('v',r),x.quit())); QTimer.singleShot(t,x.quit); x.exec(); return b.get('v')
def wait(ms):
    x=QEventLoop(); QTimer.singleShot(ms,x.quit); x.exec()
wait(3500)
print("BEFORE", js("document.getElementById('screen-home').innerText.indexOf('연동테스트팀')"))
n=js("KOVO_APP.applyChunk('core', %s); KOVO_APP.render(); 1" % json.dumps(chunk, ensure_ascii=False))
wait(1200)
print("AFTER", js("document.getElementById('screen-home').innerText.indexOf('연동테스트팀')"), "gen", js("KOVO_APP.KD.gen"))
print("ROWS", js("KOVO_APP.KD.std['023']['M'].length"), "BOX", js("Object.keys(KOVO_APP.KD.box).length"))
