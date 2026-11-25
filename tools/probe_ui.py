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
# 선수 검색
js("document.querySelector('.tab-btn[data-tab=\"players\"]').click()"); wait(500)
js("var i=document.getElementById('p-q'); i.value='김'; i.dispatchEvent(new Event('input',{bubbles:true}));"); wait(600)
print("SEARCH 김", js("document.querySelectorAll('.p-row').length"))
js("var i=document.getElementById('p-q'); i.value=''; i.dispatchEvent(new Event('input',{bubbles:true}));"); wait(500)
js("document.querySelector('[data-pos=\"MB\"]').click()"); wait(500)
print("POS MB", js("document.querySelectorAll('.p-row').length"))
js("document.querySelector('[data-pos=\"\"]').click()"); wait(400)
js("document.getElementById('p-foreign').click()"); wait(500)
print("FOREIGN", js("document.querySelectorAll('.p-row').length"))
# 뉴스 종류 전환
js("document.querySelector('[data-newskind=\"ext\"]').click()"); wait(500)
print("NEWS ext", js("document.querySelectorAll('.news-item').length"), js("document.getElementById('screen-news').innerText.replace(/\\n/g,' ').slice(0,140)"))
js("document.querySelector('[data-newskind=\"press\"]').click()"); wait(400)
print("NEWS press", js("document.querySelectorAll('.news-item').length"))
# 모달 스크롤 잠금
js("document.querySelector('.tab-btn[data-tab=\"games\"]').click()"); wait(500)
js("window.scrollTo(0,300)")
y0=js("window.scrollY")
js("document.querySelector('.game-row[data-game]').click()"); wait(600)
locked=js("document.body.style.position")
js("document.querySelector('[data-close=\"modal-game\"]').click()"); wait(400)
print("SCROLL", y0, locked, js("window.scrollY"), "bodypos", json.dumps(js("document.body.style.position")))
# 시즌 변경
js("document.querySelector('.tab-btn[data-tab=\"home\"]').click(); var s=document.getElementById('home-season'); s.value='021'; s.dispatchEvent(new Event('change',{bubbles:true}));"); wait(700)
print("SEASON 021", js("document.getElementById('screen-home').innerText.indexOf('도드람 2024~2025')>=0"), js("KOVO_APP.S.season"))
