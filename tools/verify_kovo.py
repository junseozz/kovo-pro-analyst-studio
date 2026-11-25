#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KOVO 앱 실기 검증 — QtWebEngine. 사용: python3 verify_kovo.py [W] [H] [light|dark]"""
import os, sys, json
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_OPENGL', 'software')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', '--no-sandbox --disable-gpu --disable-dev-shm-usage --single-process')
os.environ.setdefault('QTWEBENGINE_DISABLE_SANDBOX', '1')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt6.QtCore import QUrl, QTimer, QEventLoop
sys.stdout.reconfigure(line_buffering=True)

HTML = '/workspace/KOVO_PRO_ANALYST_STUDIO.html'
OUT = '/workspace/work_tmp/kovo_v1/verify'
W = int(sys.argv[1]) if len(sys.argv) > 1 else 390
H = int(sys.argv[2]) if len(sys.argv) > 2 else 844
THEME = sys.argv[3] if len(sys.argv) > 3 else 'light'
ERR = []
KEEP = {}

app = QApplication.instance() or QApplication(sys.argv[:1])
prof = QWebEngineProfile('kovorun', app)
prof.setPersistentStoragePath('/workspace/work_tmp/kovo_v1/webprofile')
prof.setCachePath('/workspace/work_tmp/kovo_v1/webcache')
v = QWebEngineView()
KEEP['v'] = v

class P(QWebEnginePage):
    def javaScriptConsoleMessage(self, lvl, m, li, s):
        if lvl == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            m = str(m)
            if not ('CORS' in m or 'net::ERR' in m or 'ERR_BLOCKED' in m or 'Access-Control' in m):
                ERR.append(m[:240])
p = P(prof, v); v.setPage(p); v.resize(W, H)
for a in (QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
          QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls):
    p.settings().setAttribute(a, True)
v.show()
loop = QEventLoop(); v.loadFinished.connect(lambda ok: loop.quit())
v.load(QUrl.fromLocalFile(HTML)); loop.exec()

def wait(ms):
    x = QEventLoop(); QTimer.singleShot(ms, x.quit); x.exec()
def js(c, t=30000):
    box = {}
    x = QEventLoop()
    v.page().runJavaScript(c, 0, lambda r: (box.__setitem__('v', r), x.quit()))
    QTimer.singleShot(t, x.quit); x.exec()
    return box.get('v')
def shot(name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, '%s_%sx%s_%s.png' % (name, W, H, THEME))
    v.grab().save(path)
    return path

wait(4000)
print('TITLE', js('document.title'))
if THEME != 'light':
    js("document.documentElement.setAttribute('data-theme','%s'); window.KOVO_APP&&KOVO_APP.render();" % THEME)
    wait(600)

TABS = ['home', 'players', 'games', 'teams', 'lab', 'fut', 'news', 'ai']
for t in TABS:
    js("document.querySelector('.tab-btn[data-tab=\"%s\"]').click();" % t)
    wait(500)
    info = js("""(function(){var s=document.getElementById('screen-%s');
      var n=s.innerText.length, over=s.scrollWidth-s.clientWidth;
      var clipped=0, els=s.querySelectorAll('*');
      for(var i=0;i<els.length;i++){var e=els[i]; if(e.children.length===0&&e.innerText&&e.scrollWidth>e.clientWidth+2) clipped++;}
      return JSON.stringify({len:n, over:over, clipped:clipped, head:s.innerText.slice(0,60).replace(/\\n/g,' ')});})()""" % t)
    print('TAB', t, info)
    shot(t)

# 선수 모달
js("document.querySelector('.tab-btn[data-tab=\"players\"]').click();")
wait(400)
r = js("""(function(){var r=document.querySelector('.p-row'); if(!r) return 'nop'; r.click(); return 'ok';})()""")
wait(700)
print('PLAYER MODAL', r, js("""(function(){var m=document.getElementById('modal-player');return m.classList.contains('open')+'/'+document.getElementById('modal-player-body').innerText.length;})()"""))
shot('player_modal')
js("document.querySelector('[data-close=\"modal-player\"]').click();")
wait(300)
print('CLOSED', js("!document.getElementById('modal-player').classList.contains('open')"), 'scrollY', js('window.scrollY'))

# 경기 모달
js("document.querySelector('.tab-btn[data-tab=\"games\"]').click();")
wait(500)
r = js("""(function(){var r=document.querySelector('.game-row[data-game]'); if(!r) return 'nop'; r.click(); return r.getAttribute('data-game');})()""")
wait(800)
print('GAME MODAL', r, js("""(function(){var m=document.getElementById('modal-game');return m.classList.contains('open')+'/'+document.getElementById('modal-game-body').innerText.length;})()"""))
shot('game_modal')
js("document.querySelector('[data-close=\"modal-game\"]').click();")
wait(250)

# 여자부
js("document.querySelector('.league-btn[data-gender=\"W\"]').click(); document.querySelector('.tab-btn[data-tab=\"home\"]').click();")
wait(600)
print('WOMEN HOME', js("document.getElementById('screen-home').innerText.length"))
shot('home_women')
js("document.querySelector('.league-btn[data-gender=\"M\"]').click();")
wait(300)

# 대비 측정 (본문/카드)
print('CONTRAST', js("""(function(){
  function lum(c){var m=c.match(/[\\d.]+/g); if(!m) return null;
    var r=parseFloat(m[0])/255,g=parseFloat(m[1])/255,b=parseFloat(m[2])/255;
    function f(x){return x<=0.03928?x/12.92:Math.pow((x+0.055)/1.055,2.4);}
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b);}
  var body=getComputedStyle(document.body);
  var card=document.querySelector('.card');
  var cs=card?getComputedStyle(card):body;
  var pairs=[[body.color, body.backgroundColor],[cs.color, cs.backgroundColor]];
  return pairs.map(function(p){var a=lum(p[0]),b=lum(p[1]);
    if(a==null||b==null) return null; var L1=Math.max(a,b),L2=Math.min(a,b);
    return +((L1+0.05)/(L2+0.05)).toFixed(2);}).join(',');})()"""))
print('H-OVERFLOW', js('document.documentElement.scrollWidth-document.documentElement.clientWidth'))
print('BODY-WEIGHTS', js("""(function(){var bad=[],els=document.querySelectorAll('*');
  for(var i=0;i<els.length;i++){var w=getComputedStyle(els[i]).fontWeight; if(w!=='400'&&w!=='normal') bad.push(els[i].tagName+':'+w);}
  return bad.length+' '+bad.slice(0,6).join(',');})()"""))
print('ERRORS', json.dumps(ERR[:10], ensure_ascii=False))
print('DONE')
