import asyncio, sys, json
from playwright.async_api import async_playwright

URL = "file:///workspace/KOVO_PRO_ANALYST_STUDIO.html"
OUT = "/workspace/work_tmp/kovo_v1/verify"

async def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        errs, cons = [], []
        pg.on("console", lambda m: cons.append((m.type, m.text)) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(URL, wait_until="load")
        await pg.wait_for_timeout(2500)
        print("TITLE", await pg.title())
        for tab in ["home","players","games","teams","lab","fut","news","ai"]:
            await pg.click(f'.tab-btn[data-tab="{tab}"]')
            await pg.wait_for_timeout(350)
            txt = await pg.inner_text(f"#screen-{tab}")
            print(f"TAB {tab}: {len(txt)} chars | {txt[:70].replace(chr(10),' ')}")
            await pg.screenshot(path=f"{OUT}/{tab}_390.png", full_page=False)
        # 선수 모달
        await pg.click('.tab-btn[data-tab="players"]'); await pg.wait_for_timeout(400)
        await pg.click('.p-row'); await pg.wait_for_timeout(500)
        ok = await pg.is_visible("#modal-player.open")
        print("PLAYER MODAL", ok, len(await pg.inner_text("#modal-player-body")))
        await pg.screenshot(path=f"{OUT}/player_modal_390.png")
        sy = await pg.evaluate("window.scrollY")
        await pg.click('[data-close="modal-player"]'); await pg.wait_for_timeout(300)
        print("MODAL CLOSED", not await pg.is_visible("#modal-player.open"), "scrollY", await pg.evaluate("window.scrollY"))
        # 경기 모달
        await pg.click('.tab-btn[data-tab="games"]'); await pg.wait_for_timeout(400)
        rows = await pg.query_selector_all('.game-row')
        print("GAME ROWS", len(rows))
        if rows:
            await rows[0].click(); await pg.wait_for_timeout(600)
            print("GAME MODAL", await pg.is_visible("#modal-game.open"), len(await pg.inner_text("#modal-game-body")))
            await pg.screenshot(path=f"{OUT}/game_modal_390.png")
            await pg.click('[data-close="modal-game"]'); await pg.wait_for_timeout(200)
        # 여자부
        await pg.click('.league-btn[data-gender="W"]'); await pg.wait_for_timeout(500)
        await pg.click('.tab-btn[data-tab="home"]'); await pg.wait_for_timeout(400)
        print("WOMEN home", len(await pg.inner_text("#screen-home")))
        await pg.screenshot(path=f"{OUT}/home_women_390.png")
        # 다크
        await pg.click("#theme-btn"); await pg.wait_for_timeout(400)
        await pg.screenshot(path=f"{OUT}/home_dark_390.png")
        # 오버플로 검사 (가로 스크롤)
        ov = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        print("H-OVERFLOW", ov)
        # 데스크톱
        await pg.set_viewport_size({"width": 1440, "height": 900}); await pg.wait_for_timeout(400)
        for tab in ["home","players","games","teams","lab","fut","news","ai"]:
            await pg.click(f'.tab-btn[data-tab="{tab}"]'); await pg.wait_for_timeout(250)
            await pg.screenshot(path=f"{OUT}/{tab}_1440.png")
        print("CONSOLE", cons[:8])
        print("PAGEERRORS", errs[:8])
        await b.close()

asyncio.run(main())
