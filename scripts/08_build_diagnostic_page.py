#!/usr/bin/env python
"""Build a self-contained, offline diagnostic page from experiment outputs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
OUTPUT = ROOT / "dashboard" / "predictor_diagnostics.html"


def records(name: str) -> list[dict]:
    return json.loads(pd.read_csv(TABLES / name).to_json(orient="records", force_ascii=False))


def build() -> Path:
    data = {
        "summary": records("predictor_comparison.csv"),
        "maps": records("predictor_by_map.csv"),
        "months": records("predictor_by_month.csv"),
        "calibration": records("predictor_calibration.csv"),
        "split": json.loads((TABLES / "predictor_split.json").read_text(encoding="utf-8")),
    }
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    template = r'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chẩn đoán mô hình dự đoán thắng Valorant</title>
<style>
:root{--bg:#0e1923;--surface:#172633;--line:#344451;--ink:#f2f0eb;--muted:#afbec7;--teal:#27c8b5;--red:#ff5a67;--amber:#f3bc58}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Arial,sans-serif}a{color:var(--teal)}
.wrap{max-width:1160px;margin:auto;padding:32px 24px 72px}.hero{border-left:4px solid var(--red);padding:0 0 0 22px}.eyebrow{color:var(--red);font-size:12px;font-weight:700;letter-spacing:.13em;text-transform:uppercase}
h1{font-size:clamp(32px,4vw,52px);line-height:1.08;max-width:900px;margin:8px 0 13px}h2{font-size:25px;margin:0 0 9px}p{margin:8px 0 16px}.lead{max-width:920px;color:var(--muted);font-size:18px}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}.meta span{border:1px solid var(--line);border-radius:40px;padding:5px 11px;font-size:12px;color:var(--muted)}
nav{display:flex;gap:22px;flex-wrap:wrap;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:12px 0;margin:25px 0;color:var(--muted);font-size:13px}nav a{text-decoration:none;color:inherit}nav a:hover{color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.kpi{background:var(--surface);border:1px solid var(--line);border-radius:9px;padding:16px}.kpi strong{display:block;font-size:26px;line-height:1.15}.kpi span{display:block;font-size:12px;letter-spacing:.04em;text-transform:uppercase;margin-top:6px}.kpi small{display:block;color:var(--muted);font-size:12px;margin-top:5px}
.notice{border-left:3px solid var(--amber);background:#232b30;padding:13px 16px;margin:23px 0 34px}.notice strong{color:var(--amber)}
section{padding:28px 0;border-top:1px solid var(--line)}.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:20px}.kicker{color:var(--red);font-size:12px;font-weight:700;letter-spacing:.1em}.muted{color:var(--muted)}
.scroll{overflow-x:auto}.data{width:100%;border-collapse:collapse;margin:15px 0 8px;font-variant-numeric:tabular-nums}.data th,.data td{border-bottom:1px solid var(--line);padding:10px;text-align:right;white-space:nowrap}.data th:first-child,.data td:first-child{text-align:left}.data th{font-size:12px;color:var(--muted);font-weight:700}.data tbody tr:hover{background:var(--surface)}.data .best{color:var(--teal);font-weight:700}.data .bad{color:var(--red)}
.small{font-size:13px;color:var(--muted)}.grid{display:grid;grid-template-columns:1fr 1fr;gap:28px}.chart{width:100%;min-height:300px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px}
.legend{display:flex;gap:17px;flex-wrap:wrap;font-size:13px;color:var(--muted)}.legend b{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}.control{display:flex;align-items:center;gap:10px;margin:8px 0 6px}select{background:var(--surface);color:var(--ink);border:1px solid var(--line);padding:7px 10px;border-radius:5px;font:inherit}
footer{border-top:1px solid var(--line);padding-top:18px;color:var(--muted);font-size:13px}code{color:var(--teal)}
@media(max-width:800px){.kpis{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}.wrap{padding:20px 14px 50px}.data{font-size:13px}.data th,.data td{padding:8px}}
</style></head><body><div class="wrap">
<header class="hero"><div class="eyebrow">Khai phá dữ liệu Valorant · Chẩn đoán ngoài mẫu</div>
<h1>Đội hình Agent dự đoán thắng đến đâu?</h1>
<p class="lead">So sánh Random Forest, AdaBoost và hồi quy logistic trên những ván diễn ra sau tập huấn luyện. Trang này đọc trực tiếp kết quả pipeline, chỉ ra mức cải thiện, độ bất định và nơi mô hình suy giảm.</p>
<div class="meta"><span id="dateRange"></span><span id="datasetSize"></span><span>Đơn vị: một ván có hai đội hình hợp lệ</span><span>Chỉ dùng map, patch và Agent trước kết quả</span></div></header>
<nav aria-label="Mục lục"><a href="#quality">01 Chất lượng</a><a href="#comparison">02 So sánh</a><a href="#maps">03 Theo map</a><a href="#time">04 Theo tháng</a><a href="#calibration">05 Hiệu chỉnh</a><a href="#limits">06 Cách đọc</a></nav>
<div class="kpis" id="kpis"></div><div class="notice" id="bias"></div>
<section id="quality"><div class="kicker">01 · CHẤT LƯỢNG THỰC NGHIỆM</div><h2>Mỗi ván chỉ có một dự đoán</h2>
<p>Train và test tách theo <strong>ngày trọn vẹn</strong>; không có GameID hoặc MatchID nằm ở cả hai tập. Đội đích chọn theo thứ tự chữ cái của mã đội, tránh học cách xếp thứ tự Team1 trong dữ liệu gốc.</p>
<p id="patchDrift"></p></section>
<section id="comparison"><div class="kicker">02 · SO SÁNH MÔ HÌNH</div><h2>Cải thiện nhỏ và chưa chắc chắn</h2>
<p class="muted">Log loss và Brier càng thấp càng tốt; AUC 0,5 tương đương xếp hạng ngẫu nhiên. Cột Δ là log loss của mốc tần suất train trừ log loss mô hình; dương là tốt hơn. Khoảng tin cậy 95% lấy mẫu lại theo MatchID.</p>
<div class="scroll"><table class="data" aria-label="Bảng mô hình" id="modelTable"><thead><tr><th>Mô hình</th><th>Accuracy</th><th>AUC</th><th>Log loss</th><th>Brier</th><th>Δ log loss</th><th>CI 95% của Δ</th></tr></thead><tbody></tbody></table></div>
<p class="small">So sánh khoảng tin cậy của Δ log loss với 0 để đánh giá mức cải thiện so với mốc.</p></section>
<section id="maps"><div class="section-head"><div><div class="kicker">03 · PHÂN TÍCH LỖI</div><h2>Khác biệt lớn giữa các bản đồ</h2></div><div class="control"><label for="mapModel">Mô hình</label><select id="mapModel"><option>Random Forest</option><option>AdaBoost</option></select></div></div>
<div class="scroll"><table class="data" aria-label="Hiệu năng theo bản đồ" id="mapTable"><thead><tr><th>Bản đồ</th><th>Số ván test</th><th>Tỷ lệ thắng</th><th>AUC</th><th>Log loss</th><th>Δ so với mốc</th></tr></thead><tbody></tbody></table></div><p class="small">Fracture chỉ có 99 ván test. Không xếp hạng chiến thuật từ một nhóm nhỏ hoặc từ Δ của một map riêng lẻ.</p></section>
<section id="time"><div class="kicker">04 · DỊCH CHUYỂN THEO THỜI GIAN</div><h2>Hiệu năng thay đổi giữa các tháng</h2><p class="muted">Δ log loss so với mốc train theo tháng trong tập test. Điểm cuối có ít ván hơn; biểu đồ mô tả sự thay đổi, không thay thế kiểm định độc lập.</p>
<div class="chart" id="monthChart" role="img" aria-label="Biểu đồ mức giảm log loss theo tháng"></div><div class="legend"><span><b style="background:var(--teal)"></b>Random Forest</span><span><b style="background:var(--red)"></b>AdaBoost</span><span>Đường ngang: mốc không cải thiện</span></div></section>
<section id="calibration"><div class="kicker">05 · HIỆU CHỈNH XÁC SUẤT</div><h2>Điểm 60% có đáng tin?</h2><p class="muted">Mỗi điểm là một phân vị dự đoán trên tập test. So sánh xác suất trung bình với tỷ lệ thắng thực tế trong nhóm đó; đường chéo là hiệu chỉnh lý tưởng.</p>
<div class="chart" id="calChart" role="img" aria-label="Biểu đồ hiệu chỉnh xác suất"></div><div class="legend"><span><b style="background:var(--teal)"></b>Random Forest</span><span><b style="background:var(--red)"></b>AdaBoost</span><span>Đường chéo: lý tưởng</span></div></section>
<section id="limits"><div class="kicker">06 · CÁCH ĐỌC ĐÚNG</div><h2>Tín hiệu dự đoán khác tác động chiến thuật</h2>
<p>Mô hình không thấy sức mạnh đội, lịch sử gần đây, chiến thuật hoặc tình trạng người chơi. Những yếu tố đó vừa ảnh hưởng chọn Agent, vừa ảnh hưởng thắng trận. Vì vậy kết quả không chứng minh Agent gây ra chiến thắng.</p>
<p>Snapshot dừng ở tháng 01/2022; meta hiện tại có thể khác. Repo gốc chưa ghi rõ upstream của file SQLite. Muốn kiểm định thêm cần các giai đoạn test mới và dữ liệu đội có trước trận.</p></section>
<footer>Nguồn: <code>data/raw/valorant.sqlite</code> và <code>outputs/tables/predictor_*.csv</code> trong repo. Sinh bằng <code>scripts/07_compare_predictors.py</code> và <code>scripts/08_build_diagnostic_page.py</code>.</footer></div>
<script>const DATA=__DATA__;
const fmt=(x,n=3)=>Number(x).toFixed(n).replace('.',','); const pct=x=>fmt(x*100,1)+'%'; const signed=x=>(x>0?'+':'')+fmt(x,4);
const split=DATA.split, summary=DATA.summary;
document.querySelector('#dateRange').textContent=split.test_first+' đến '+split.test_last;
document.querySelector('#datasetSize').textContent=split.n_train.toLocaleString('vi-VN')+' train / '+split.n_test.toLocaleString('vi-VN')+' test';
const best=summary.find(x=>x.model==='Random Forest'); const unseen=split.unseen_patch_test_games;
document.querySelector('#kpis').innerHTML=[
 ['Ván test',split.n_test.toLocaleString('vi-VN'),'trên '+split.n_test_matches.toLocaleString('vi-VN')+' trận'],
 ['AUC Random Forest',fmt(best.test_roc_auc),'0,5 là ngẫu nhiên'],
 ['Δ log loss',signed(best.delta_log_loss_vs_baseline),'CI 95%: '+signed(best.delta_ci_low)+' đến '+signed(best.delta_ci_high)],
 ['Patch chưa thấy',pct(unseen/split.n_test),unseen.toLocaleString('vi-VN')+' ván test']]
 .map(([v,a,b])=>'<div class="kpi"><strong>'+a+'</strong><span>'+v+'</span><small>'+b+'</small></div>').join('');
document.querySelector('#bias').innerHTML='<strong>Thiên lệch nhãn đã xử lý:</strong> Team1 thắng '+pct(split.raw_team1_win_rate)+' trong snapshot. Nếu dùng Team1 làm đội đích, mô hình có thể học thứ tự ghi dữ liệu. Sau chọn mã đội theo chữ cái, tỷ lệ thắng là '+pct(split.positive_rate_train)+' ở train và '+pct(split.positive_rate_test)+' ở test.';
document.querySelector('#patchDrift').innerHTML='<strong>Dịch chuyển patch:</strong> '+unseen.toLocaleString('vi-VN')+' / '+split.n_test.toLocaleString('vi-VN')+' ván test ('+pct(unseen/split.n_test)+') thuộc '+split.unseen_patch_test_labels.length+' patch chưa xuất hiện trong train. Đây là phép thử tổng quát hóa thực tế nhưng làm kết quả khó hơn.';
document.querySelector('#modelTable tbody').innerHTML=summary.map(x=>'<tr><td>'+x.model+'</td><td>'+pct(x.test_accuracy)+'</td><td>'+fmt(x.test_roc_auc)+'</td><td>'+fmt(x.test_log_loss,4)+'</td><td>'+fmt(x.test_brier,4)+'</td><td class="'+(x.delta_log_loss_vs_baseline>0?'best':'bad')+'">'+signed(x.delta_log_loss_vs_baseline)+'</td><td>'+signed(x.delta_ci_low)+' đến '+signed(x.delta_ci_high)+'</td></tr>').join('');
function maps(){const model=document.querySelector('#mapModel').value;document.querySelector('#mapTable tbody').innerHTML=DATA.maps.filter(x=>x.model===model).map(x=>'<tr><td>'+x.Map+'</td><td>'+x.n_games.toLocaleString('vi-VN')+'</td><td>'+pct(x.win_rate)+'</td><td>'+fmt(x.roc_auc)+'</td><td>'+fmt(x.log_loss,4)+'</td><td class="'+(x.delta_log_loss_vs_baseline>0?'best':'bad')+'">'+signed(x.delta_log_loss_vs_baseline)+'</td></tr>').join('')};document.querySelector('#mapModel').addEventListener('change',maps);maps();
function svgLine(container,series,xValues,yMin,yMax,xLabel,yLabel,reference){const W=980,H=300,L=74,R=20,T=22,B=58;const X=i=>L+24+i*(W-L-R-48)/(xValues.length-1);const Y=v=>T+(yMax-v)*(H-T-B)/(yMax-yMin);let html='<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:auto" xmlns="http://www.w3.org/2000/svg">';
 for(let i=0;i<5;i++){let v=yMin+i*(yMax-yMin)/4;html+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#344451"/><text x="'+(L-8)+'" y="'+(Y(v)+4)+'" text-anchor="end" fill="#afbec7" font-size="13">'+fmt(v,3)+'</text>'}
 if(reference!==null)html+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(reference)+'" y2="'+Y(reference)+'" stroke="#f3bc58" stroke-dasharray="6 5"/>';
 xValues.forEach((v,i)=>html+='<text x="'+X(i)+'" y="'+(H-33)+'" text-anchor="middle" fill="#afbec7" font-size="13">'+v+'</text>');
 series.forEach(s=>{html+='<polyline fill="none" stroke="'+s.color+'" stroke-width="3" points="'+s.values.map((v,i)=>X(i)+','+Y(v)).join(' ')+'"/>';s.values.forEach((v,i)=>html+='<circle cx="'+X(i)+'" cy="'+Y(v)+'" r="4" fill="'+s.color+'"/>')});
 html+='<text x="'+(W/2)+'" y="'+(H-4)+'" text-anchor="middle" fill="#afbec7" font-size="14">'+xLabel+'</text><text transform="translate(17 '+H/2+') rotate(-90)" text-anchor="middle" fill="#afbec7" font-size="14">'+yLabel+'</text></svg>';container.innerHTML=html}
const months=[...new Set(DATA.months.map(x=>x.month))];const modelColors={'Random Forest':'#27c8b5',AdaBoost:'#ff5a67'};
svgLine(document.querySelector('#monthChart'),['Random Forest','AdaBoost'].map(model=>({color:modelColors[model],values:months.map(m=>DATA.months.find(x=>x.model===model&&x.month===m).delta_log_loss_vs_baseline)})),months,Math.min(-.005,...DATA.months.filter(x=>x.model==='Random Forest'||x.model==='AdaBoost').map(x=>x.delta_log_loss_vs_baseline))-.002,Math.max(.005,...DATA.months.filter(x=>x.model==='Random Forest'||x.model==='AdaBoost').map(x=>x.delta_log_loss_vs_baseline))+.002,'Tháng test','Δ log loss',0);
const cal=DATA.calibration;const deciles=[...new Set(cal.map(x=>x.decile))];const W=980,H=300,L=74,R=20,T=22,B=58;const X=v=>L+(v-.35)*(W-L-R)/.35,Y=v=>T+(.7-v)*(H-T-B)/.35;let c='<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:auto" xmlns="http://www.w3.org/2000/svg">';
for(let v=.35;v<=.701;v+=.05){c+='<line x1="'+X(v)+'" x2="'+X(v)+'" y1="'+T+'" y2="'+(H-B)+'" stroke="#344451"/><line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="#344451"/><text x="'+X(v)+'" y="'+(H-33)+'" text-anchor="middle" fill="#afbec7" font-size="12">'+fmt(v,2)+'</text><text x="'+(L-8)+'" y="'+(Y(v)+4)+'" text-anchor="end" fill="#afbec7" font-size="12">'+fmt(v,2)+'</text>'}
c+='<line x1="'+X(.35)+'" y1="'+Y(.35)+'" x2="'+X(.7)+'" y2="'+Y(.7)+'" stroke="#f3bc58" stroke-dasharray="6 5"/>';
for(const model of ['Random Forest','AdaBoost']){const rows=cal.filter(x=>x.model===model);c+='<polyline fill="none" stroke="'+modelColors[model]+'" stroke-width="3" points="'+rows.map(x=>X(x.mean_predicted)+','+Y(x.observed_win_rate)).join(' ')+'"/>';rows.forEach(x=>c+='<circle cx="'+X(x.mean_predicted)+'" cy="'+Y(x.observed_win_rate)+'" r="4" fill="'+modelColors[model]+'"/>')}
c+='<text x="'+W/2+'" y="'+(H-4)+'" text-anchor="middle" fill="#afbec7" font-size="14">Xác suất dự đoán</text><text transform="translate(17 '+H/2+') rotate(-90)" text-anchor="middle" fill="#afbec7" font-size="14">Tỷ lệ thắng</text></svg>';document.querySelector('#calChart').innerHTML=c;
</script></body></html>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(template.replace("__DATA__", payload), encoding="utf-8")
    return OUTPUT


if __name__ == "__main__":
    print(build())
