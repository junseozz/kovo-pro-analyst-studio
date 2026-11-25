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
print("META", js("JSON.stringify(KOVO_APP.KD.meta)"))
print("SEASONS", js("KOVO_APP.KD.seasons.map(s=>s.c+':'+s.n).join(' | ')"))
js("document.querySelector('.league-btn[data-gender=\"W\"]').click()"); wait(600)
print("W teams", js("document.querySelectorAll('.team-card').length"), js("document.getElementById('screen-home').innerText.slice(0,120).replace(/\\n/g,' ')"))
js("document.querySelector('.league-btn[data-gender=\"M\"]').click()"); wait(400)
# 2025-26 시즌
js("var s=document.querySelector('#home-season'); s.value='022'; s.dispatchEvent(new Event('change',{bubbles:true}));"); wait(700)
print("2022 season", js("document.getElementById('screen-home').innerText.slice(0,90).replace(/\\n/g,' ')"))
# 퓨처스
js("document.querySelector('.tab-btn[data-tab=\"fut\"]').click()"); wait(600)
print("FUT", js("document.getElementById('screen-fut').innerText.replace(/\\n/g,' ').slice(0,400)"))
js("window.scrollTo(0,1200)"); wait(400); v.grab().save('/workspace/work_tmp/kovo_v1/verify/fut2.png')
js("window.scrollTo(0,3000)"); wait(400); v.grab().save('/workspace/work_tmp/kovo_v1/verify/fut3.png')
# AI 테스트
js("document.querySelector('.tab-btn[data-tab=\"ai\"]').click()"); wait(500)
for q in ["득점 1위","케트진스키 어때","오늘 경기"]:
    js("KOVO_APP.S.chat=[]; var i=document.getElementById('ai-input'); if(i){i.value=%s; document.getElementById('ai-send').click();} 1" % json.dumps(q))
    wait(700)
    print("AI", json.dumps(q), js("JSON.stringify(KOVO_APP.S.chat).slice(0,300)"))
