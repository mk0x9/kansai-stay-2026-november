# Jalan extraction helpers. Load inside a browser-use heredoc with:
#   exec(open("/Users/mikhail/code/jalan-trip-2026-november/work/jalan_lib.py").read())
import json, re

SEARCH_BASE = "https://www.jalan.net/{ken}/{lrg}/"
DATE_RANGES = {
    "16-18": (16, 2),
    "17-19": (17, 2),
    "16-19": (16, 3),
}


def search_url(ken, lrg, day, nights, max_price=60000, page=1):
    q = (f"?stayYear=2026&stayMonth=11&stayDay={day}&dateUndecided=0&stayCount={nights}"
         f"&roomCount=1&adultNum=2&roomCrack=200000&yadRk=1&careOnsen=1"
         f"&minPrice=0&maxPrice={max_price}&screenId=UWW1402&distCd=01&rootCd=04")
    return SEARCH_BASE.format(ken=ken, lrg=lrg) + (f"page{page}.html" if page > 1 else "") + q


LIST_JS = r"""(()=>{
const num=s=>s?+s.replace(/[^\d]/g,''):null;
const items=[...document.querySelectorAll('li.js-searchResultItem')].map(li=>{
  const q=s=>li.querySelector(s);const tx=s=>(q(s)||{}).textContent?.trim().replace(/\s+/g,' ')||null;
  const plans=[...li.querySelectorAll('tr.js-searchYadoRoomPlanCd')].map(tr=>{
    const a=tr.querySelector('a.p-searchResultItem__planName');const t=s=>(tr.querySelector(s)||{}).textContent?.trim().replace(/\s+/g,' ')||null;
    const h=a?a.getAttribute('href'):'';const g=k=>(h.match(new RegExp(k+'=(\\w+)'))||[])[1]||null;
    return {name:a?a.textContent.trim().replace(/\s+/g,' '):null, planCd:g('planCd'), roomTypeCd:g('roomTypeCd'),
      room:t('.p-searchResultItem__verticalLabel--room'), meal:t('.p-searchResultItem__verticalLabel--meal'),
      labels:[...tr.querySelectorAll('.p-searchResultItem__horizontalLabel')].map(e=>e.textContent.trim()),
      perPerson:num(t('.p-searchResultItem__perPerson')), total:num(t('.p-searchResultItem__total')),
      url:a?a.href:null};
  });
  const more=[...li.querySelectorAll('a')].find(a=>/宿泊プランをもっとみる/.test(a.textContent));
  return {
    yadNo: li.id.replace('yadNo',''),
    name: tx('.p-searchResultItem__facilityName'),
    catch: tx('.p-searchResultItem__catchPhrase'),
    area: tx('.p-searchResultItem__areaValues'),
    lowestTotal: num(tx('.p-searchResultItem__lowestPriceValue')),
    rating: parseFloat(tx('.p-searchResultItem__summaryaverage-num'))||null,
    reviews: num(tx('.p-searchResultItem__summarykuchikomi__totalNumber')),
    highlyRated: tx('.p-searchResultItem__highlyRated strong'),
    description: tx('.p-searchResultItem__description'),
    access: tx('.p-searchResultItem__accessValue'),
    thumbs: [...li.querySelectorAll('.p-searchResultItem__thumbnail img')].map(i=>i.src),
    plans, morePlans: more?num(more.textContent):0,
  }});
const next=[...document.querySelectorAll('a.next')].length>0;
return {count:num((document.querySelector('.jlnpc-listInformation--count')||{}).textContent||''), items, hasNext: next};
})()"""


def extract_list():
    return js(LIST_JS)


DETAIL_JS = r"""(()=>{
const imgs=[...new Set([...document.querySelectorAll('img')].map(i=>i.src||i.dataset.src||'').filter(u=>/cdn\.jalan\.jp\/jalan\/images\/pict[0-9]*[LMS]?\/Y/.test(u)).map(u=>u.replace('/pictM/','/pictL/').replace('/pictS/','/pictL/')))];
const caps=[...document.querySelectorAll('img')].filter(i=>/pict/.test(i.src)&&i.alt).map(i=>[i.src.replace('/pictM/','/pictL/'),i.alt]);
const m=document.documentElement.innerHTML.match(/center=(-?[\d.]+)(?:,|%2C)(-?[\d.]+)/);
return {text: document.body.innerText, imgs, caps, coords: m?[+m[1],+m[2]]:null};
})()"""


def _after(text, label, n=1):
    m = re.search(r"(?m)^" + re.escape(label) + r"\t([^\n]*)", text)
    return m.group(1).strip() if m else None


def parse_detail(text):
    d = {}
    d["address"] = _after(text, "住所")
    d["parking"] = _after(text, "パーキング")
    d["onsen"] = _after(text, "温泉")
    d["private_bath"] = _after(text, "貸切風呂")
    m = re.search(r"露天\t内湯\tサウナ\n[^\n]*\n([\d\t ]+)\n", text)
    if m:
        v = [int(x) for x in m.group(1).split()]
        if len(v) == 9:
            d["rotenburo_mfx"], d["indoor_mfx"], d["sauna_mfx"] = v[0:3], v[3:6], v[6:9]
    m = re.search(r"風呂利用条件\t(.*?)\n・基本情報", text, re.S)
    d["bath_notes"] = m.group(1).strip() if m else None
    m = re.search(r"洋室\t和室\t和洋室\tその他\t総部屋数\n([^\n]+)", text)
    d["rooms"] = m.group(1).strip() if m else None
    m = re.search(r"チェックイン時間\t([^ ※\n]+)", text); d["checkin"] = m.group(1) if m else None
    m = re.search(r"チェックアウト時間\t([^ ※\n]+)", text); d["checkout"] = m.group(1) if m else None
    m = re.search(r"クチコミ評価\n.*?総合\n([\d.\-]+)\nクチコミ\t([\d,]+)件(.*?)（「普通", text, re.S)
    if m:
        d["rating"] = m.group(1)
        d["reviews"] = int(m.group(2).replace(",", ""))
        block = m.group(3)
        for k, lab in [("r_room", "部屋"), ("r_bath", "風呂"), ("r_breakfast", "料理（朝食）"),
                       ("r_dinner", "料理（夕食）"), ("r_service", "接客・サービス"), ("r_clean", "清潔感")]:
            mm = re.search(re.escape(lab) + r"\t([\d.\-]+)", block)
            d[k] = mm.group(1) if mm else None
    m = re.search(r"\n([^\n]*高評価[^\n]*)\n", text); d["highly_rated"] = m.group(1).strip() if m else None
    m = re.search(r"高評価したクチコミ\n\n(.*?)\n\n", text, re.S); d["review_highlight"] = m.group(1).strip() if m else None
    m = re.search(r"すべての写真をみる\n\n(.*?)\n\n宿泊のご予約", text, re.S); d["pr_text"] = m.group(1).strip() if m else None
    m = re.search(r"サービス&レジャー\n（手配含む）\t([^\n]*)", text); d["services"] = m.group(1) if m else None
    m = re.search(r"施設内容\t([^\n]*)", text); d["facilities"] = m.group(1) if m else None
    m = re.search(r"現地で利用可能なクレジットカード\t([^\n]*)", text); d["cards"] = m.group(1) if m else None
    return d


def extract_detail(yad_no):
    goto_url(f"https://www.jalan.net/yad{yad_no}/"); wait_for_load()
    r = js(DETAIL_JS)
    d = parse_detail(r["text"])
    d["yadNo"] = yad_no
    d["url"] = f"https://www.jalan.net/yad{yad_no}/"
    d["images"] = r["imgs"][:12]
    d["image_captions"] = r["caps"][:12]
    return d


# --- Per-worker tab: each worker owns one background tab and its own CDP session,
# so concurrent workers never touch the daemon's shared "current tab".
import time


class Tab:
    def __init__(self, target_id=None):
        self.tid = target_id or cdp("Target.createTarget", url="about:blank", background=True)["targetId"]
        self.sid = cdp("Target.attachToTarget", targetId=self.tid, flatten=True)["sessionId"]

    def js(self, expr, timeout=180):
        r = cdp("Runtime.evaluate", session_id=self.sid, _response_timeout=timeout, expression=expr, returnByValue=True, awaitPromise=True)
        if r.get("exceptionDetails"):
            raise RuntimeError(str(r["exceptionDetails"])[:500])
        return r.get("result", {}).get("value")

    def goto(self, url, timeout=25.0):
        cdp("Page.navigate", session_id=self.sid, url=url)
        time.sleep(0.4)
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                st = self.js("[document.readyState, location.href, !!(document.body && /宿番号|宿泊プラン|件の宿泊プラン|検索結果/.test(document.body.innerText))]")
                if st[1] != "about:blank" and (st[0] == "complete" or (st[0] == "interactive" and st[2])):
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        return False

    def close(self):
        try: cdp("Target.detachFromTarget", sessionId=self.sid)
        except Exception: pass
        cdp("Target.closeTarget", targetId=self.tid)


FETCH_JS = r"""(async(urls, conc)=>{const dec=new TextDecoder('shift_jis');const out=new Array(urls.length);let i=0;
  async function worker(){while(i<urls.length){const k=i++;try{const res=await fetch(urls[k],{credentials:'include'});
    out[k]={url:urls[k],status:res.status,html:dec.decode(await res.arrayBuffer())};}catch(e){out[k]={url:urls[k],status:0,error:String(e)}}
    await new Promise(r=>setTimeout(r,150+Math.random()*250));}}
  await Promise.all(Array.from({length:conc},worker));return out;})"""


def fetch_many(tab, urls, conc=4):
    """Fetch same-origin pages inside the tab (Shift_JIS-decoded HTML), `conc` in flight."""
    return tab.js(FETCH_JS + "(%s,%d)" % (json.dumps(urls), conc))


# --- Fetch-and-parse inside the page: returns compact JSON instead of raw HTML.
PARSE_FETCH_JS = r"""(async(urls, conc, kind)=>{const dec=new TextDecoder('shift_jis');const out=new Array(urls.length);let i=0;
const T=(r,s)=>{const e=r.querySelector(s);return e?e.textContent.replace(/\s+/g,' ').trim():null};
const num=s=>s?+String(s).replace(/[^\d]/g,''):null;
const parsers={
 planlist:(d,u)=>[...d.querySelectorAll('li.p-planCassette')].map(li=>({
   planName:T(li,'.p-planCassette__header')||T(li,'.p-searchResultItem__header'),
   meal:T(li,'.p-mealType__value'),
   desc:T(li,'.p-searchResultItem__description'),
   rooms:[...li.querySelectorAll('tr.js-searchYadoRoomPlanCd')].map(tr=>{const m=tr.id.match(/yd(\d+)pc(\d+)rc(\d+)/)||[];const a=tr.querySelector('a.p-searchResultItem__planName');
     return {yadNo:m[1],planCd:m[2],roomTypeCd:m[3],roomName:a?a.textContent.replace(/\s+/g,' ').trim():null,
       roomLabels:[...tr.querySelectorAll('.p-searchResultItem__verticalLabel')].map(e=>e.textContent.trim()),
       total:num(T(tr,'.p-searchResultItem__total')),url:a?new URL(a.getAttribute('href'),location.origin).href:null}})})),
 plandetail:(d,u)=>({
   meal:T(d,'.p-planOverview__meal'), roomStyle:T(d,'.jlnpc-planDetailInfo__planTitle__roomIcon'),
   roomName:T(d,'.jlnpc-planDetailInfo__planTitle__text'), roomFacilities:T(d,'.jlnpc-planDetailInfo__facilityLabel'),
   roomDetail:T(d,'.jlnpc-planDetailInfo__roomDetail'), planDetail:T(d,'.jlnpc-planDetailInfo__planDetail'),
   checkInOut:[...d.querySelectorAll('.p-planOverview__checkInOut')].map(e=>e.textContent.replace(/\s+/g,' ').trim()).join(' / '),
   note:T(d,'.p-planOverview__note'), charge:num(T(d,'.p-planOverview__charge')), cancel:T(d,'.p-planOverview__reservationWrap'),
   roomImages:[...d.querySelectorAll('.js-jlnpc-roomTypeInfo-img-slider img')].map(i=>[i.getAttribute('data-src')||i.getAttribute('src'),i.getAttribute('alt')]).filter(x=>x[0]&&/cdn\.jalan/.test(x[0])).slice(0,4),
   planImages:[...d.querySelectorAll('.js-jlnpc-planDetailInfo-img-slider img')].map(i=>[i.getAttribute('data-src')||i.getAttribute('src'),i.getAttribute('alt')]).filter(x=>x[0]&&/cdn\.jalan/.test(x[0])).slice(0,6)}),
 searchlist:(d,u)=>({count:num(T(d,'.jlnpc-listInformation--count')), hasNext:!!d.querySelector('a.next'),
   items:[...d.querySelectorAll('li.js-searchResultItem')].map(li=>({yadNo:(li.id||'').replace(/\D/g,''), name:T(li,'.p-searchResultItem__facilityName'),
     catch:T(li,'.p-searchResultItem__catchPhrase'), area:T(li,'.p-searchResultItem__areaValues'), lowestTotal:num(T(li,'.p-searchResultItem__lowestPriceValue')),
     rating:parseFloat(T(li,'.p-searchResultItem__summaryaverage-num'))||null, reviews:num(T(li,'.p-searchResultItem__summarykuchikomi__totalNumber')),
     highlyRated:T(li,'.p-searchResultItem__highlyRated strong'), description:T(li,'.p-searchResultItem__description'), access:T(li,'.p-searchResultItem__accessValue'),
     thumbs:[...li.querySelectorAll('.p-searchResultItem__thumbnail img')].map(i=>i.getAttribute('src'))}))}),
 roompage:(d,u)=>({text:(d.querySelector('#jsiRoomInfo, .shisetsu-roomsetsubi_body, main')||d.body).textContent.replace(/[ \t]+/g,' ').replace(/\n\s*\n+/g,'\n').slice(0,6000)}),
};
async function worker(){while(i<urls.length){const k=i++;try{const res=await fetch(urls[k],{credentials:'include'});const html=dec.decode(await res.arrayBuffer());
  const d=new DOMParser().parseFromString(html,'text/html');out[k]={url:urls[k],status:res.status,blocked:/エラー画面|アクセスが集中/.test(d.title+html.slice(0,3000)),data:parsers[kind](d,urls[k])};}
  catch(e){out[k]={url:urls[k],status:0,error:String(e)}}
  await new Promise(r=>setTimeout(r,150+Math.random()*250));}}
await Promise.all(Array.from({length:conc},worker));return out;})"""


def parse_fetch(tab, urls, kind, conc=4):
    return tab.js(PARSE_FETCH_JS + "(%s,%d,%s)" % (json.dumps(urls), conc, json.dumps(kind)), timeout=300)


NIGHTS = [19, 20, 21]  # Thu, Fri, Sat nights: check-in Nov 19, check-out Nov 22


def city_search_url(ken, lrg, day, nights, page=1):
    """Any accommodation type, 2 adults in 1 room, no price cap."""
    q = (f"?stayYear=2026&stayMonth=11&stayDay={day}&dateUndecided=0&stayCount={nights}"
         f"&roomCount=1&adultNum=2&roomCrack=200000&screenId=UWW1402&distCd=01&rootCd=04")
    return f"https://www.jalan.net/{ken}/LRG_{lrg}/" + (f"page{page}.html" if page > 1 else "") + q


def planlist_url(yad_no, day):
    return (f"https://www.jalan.net/yad{yad_no}/plan/?stayYear=2026&stayMonth=11&stayDay={day}&stayCount=1"
            f"&roomCount=1&adultNum=2&dateUndecided=0&roomCrack=200000")


def scrape_property(tab, yad_no, max_rows=24):
    """Detail page (navigated, for layout-aware innerText and map coords) + one plan list per night + plan details.
    Keeps, per (room type, meal), the cheapest plan for the whole stay and the cheapest for each single night."""
    tab.goto(f"https://www.jalan.net/yad{yad_no}/")
    r = tab.js(DETAIL_JS)
    prop = parse_detail(r["text"])
    prop.update(yadNo=yad_no, url=f"https://www.jalan.net/yad{yad_no}/", images=r["imgs"][:12],
                image_captions=r["caps"][:15], coords=r.get("coords"))
    lists = parse_fetch(tab, [planlist_url(yad_no, d) for d in NIGHTS], "planlist", conc=3)
    rows = {}
    for day, res in zip(NIGHTS, lists):
        for plan in (res.get("data") or []):
            for room in plan["rooms"]:
                if room["yadNo"] != str(yad_no) or not room["total"]:
                    continue
                k = (room["planCd"], room["roomTypeCd"])
                row = rows.setdefault(k, {"planCd": k[0], "roomTypeCd": k[1], "planName": plan["planName"], "meal": plan["meal"],
                                          "roomName": room["roomName"], "roomLabels": room["roomLabels"], "url": room["url"], "nightly": {}})
                row["nightly"][day] = room["total"]
    keep = {}
    def pick(tag, key, price, k):
        if price is not None and (tag, key) not in keep or (price is not None and price < keep[(tag, key)][0]):
            keep[(tag, key)] = (price, k)
    for k, row in rows.items():
        n = row["nightly"]; key = (row["roomTypeCd"], row["meal"])
        pick("full", key, sum(n.values()) / 3 if len(n) == 3 else None, k)
        for d in NIGHTS:
            pick(d, key, n.get(d), k)
    chosen = sorted({k for _, k in keep.values()}, key=lambda k: min(rows[k]["nightly"].values()))[:max_rows]
    rows = {k: rows[k] for k in chosen}
    details = parse_fetch(tab, [rows[k]["url"] for k in chosen], "plandetail", conc=4) if chosen else []
    by_plan, by_room = {}, {}
    for k, res in zip(chosen, details):
        d = res.get("data") or {}
        by_plan.setdefault(k[0], d); by_room.setdefault(k[1], d)
    for k, row in rows.items():
        p, rm = by_plan.get(k[0], {}), by_room.get(k[1], {})
        row.update(mealDetail=p.get("meal"), planDetail=p.get("planDetail"), maxNightsNote=p.get("note"), cancel=p.get("cancel"),
                   checkInOut=p.get("checkInOut"), planImages=p.get("planImages"),
                   roomStyle=rm.get("roomStyle"), roomFullName=rm.get("roomName"), roomDetail=rm.get("roomDetail"),
                   roomFacilities=rm.get("roomFacilities"), roomImages=rm.get("roomImages"))
    prop["plans"] = list(rows.values())
    prop["rowsTotal"] = len(keep)
    prop["fetches"] = 1 + len(lists) + len(chosen)
    prop["blocked"] = any(x.get("blocked") for x in lists + details)
    return prop
