import os,sys,json
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
print("W rows 023", js("KOVO_APP.KD.std['023']['W'].length"), "W players", js("KOVO_APP.KD.pr['023']['W'].length"))
print("W top", js("KOVO_APP.KD.std['023']['W'].slice(0,3).map(r=>r[0]+' '+r[2]+' '+r[3]+'승'+r[4]+'패').join(' / ')"))
js("document.querySelector('.league-btn[data-gender=\"W\"]').click()"); wait(800)
print("HOME W", js("document.getElementById('screen-home').innerText.replace(/\\n/g,' ').slice(0,260)"))
v.grab().save('/workspace/work_tmp/kovo_v1/verify/home_w2.png')
js("document.querySelector('.tab-btn[data-tab=\"players\"]').click()"); wait(700)
print("PLAYERS W", js("document.getElementById('screen-players').innerText.replace(/\\n/g,' ').slice(0,200)"))
v.grab().save('/workspace/work_tmp/kovo_v1/verify/players_w.png')
