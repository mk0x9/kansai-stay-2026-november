# Stay enrichment task (Kyoto / central Osaka, Nov 19-22 2026)

You turn scraped Jalan (Japanese) listings of hotels, ryokan, guesthouses and rentals into concise English fields for a
trip-planning map. The trip: 2 adults, 1 room, city stay in Kyoto or Osaka (near the Keihan line).

## Input
Each input file `enrich/in/K_NN.json` is a JSON array of properties. Per property:
- facts: `name`, `pref`, `area`, `address`, `access`, `catch`, `pr_text`, `onsen`, `public_baths` (counts as
  [men, women, mixed/private]), `rooms_count` (Western / Japanese / Japanese-Western / other / total), `rating`,
  `highly_rated`, `review_highlight`, `facilities`
- `rooms`: map `roomTypeCd -> {name, style_label, labels, facilities, detail}`
- `plans`: map `planCd -> {name, meal, meal_detail, detail}`

## Output
For each input file write `enrich/out/<same file name>`: a JSON array, one object per input property, same order:

```json
{
  "yadNo": "300267",
  "name_en": "Mitsui Garden Hotel Kyoto Shijo",
  "type": "hotel | ryokan | guesthouse | hostel | apartment | machiya",
  "location_en": "Short line on where it is, e.g. 'Shijo-Karasuma business district, 3 min walk to Shijo subway' (from address/access; no invented distances)",
  "strong_points": ["2-3 short bullets, most distinctive first (location, large public bath, room size, breakfast, design, service...)"],
  "watch_outs": "One short line on downsides the data shows (small rooms, shared bathroom, no front desk, far from stations...), else ''",
  "review_summary_en": "One sentence summarising review_highlight, '' if none",
  "public_bath_en": "e.g. 'Large public bath (natural hot spring) M1/F1 with sauna' or '' when none",
  "rooms": {
    "<roomTypeCd>": {
      "style": "Western | Japanese | Japanese-Western",
      "beds": "twin | double | queen | king | triple | futon | bunk | mixed | unknown",
      "size": "e.g. '18 m²' or '8 tatami' or ''",
      "view": "e.g. 'Kamo river view' or '' (only when the text says so)",
      "bathroom": "private | shared | unknown",
      "smoking": "non-smoking | smoking | unknown",
      "room_en": "Short English room name, e.g. 'Superior Twin, 22 m², non-smoking'"
    }
  },
  "plans": {
    "<planCd>": {
      "plan_name_en": "Short English plan name, max ~8 words, keep useful conditions (prepaid only, non-refundable, early bird 30 days, 2 nights+)",
      "breakfast": "buffet | set meal | in-room | none | unknown"
    }
  }
}
```

## Rules
- Use only the given data, never invent facts. Use `unknown` or `''` when the data does not say.
- `name_en`: the official English/romanized name when it appears in the data, else a careful romanization (Hotel, Inn, etc. in English).
  Drop marketing suffixes like 【...】 or ◆... from the name.
- `type`: 旅館 / 料亭旅館 → ryokan; 町家 / 一棟貸し → machiya; ゲストハウス → guesthouse; ホステル / カプセル → hostel;
  apartment-style rentals (コンドミニアム, アパートメント, 民泊, kitchen + no front desk) → apartment; everything else → hotel.
- `beds`: ツイン → twin; ダブル → double; クイーン → queen; キング → king; トリプル / 3 beds → triple; 和室 without beds → futon;
  二段ベッド → bunk; several kinds (e.g. twin + sofa bed, beds + futon) → mixed.
- `bathroom`: ユニットバス / バス・トイレ付 / シャワーブース / 客室に浴室 → private; 共同 / 共用 / バスなし トイレなし → shared;
  otherwise `unknown`. Business hotels with "バス・トイレ付" are private.
- `smoking`: 禁煙 → non-smoking; 喫煙 → smoking; 加熱式たばこ専用 → smoking (say "heated tobacco only" in room_en).
- `breakfast`: from `meal` (朝のみ / 朝・夕 means breakfast included) and the plan text: バイキング / ビュッフェ → buffet;
  定食 / 和定食 / 膳 → set meal; 食事なし / 夕のみ → none.
- Keep English short and factual. Write valid JSON (UTF-8), no markdown wrapping.
