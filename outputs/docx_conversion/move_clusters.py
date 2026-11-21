from pathlib import Path
p=Path('dashboard/public_template.html')
s=p.read_text(encoding='utf-8')
start=s.index('<section class="player-section" id="styles">')
end=s.index('</section>',start)+len('</section>')
block=s[start:end]
s=s[:start]+s[end:]
needle='<div class="player-metrics" id="playerMetrics"></div></div></section>'
assert needle in s
s=s.replace(needle,'<div class="player-metrics" id="playerMetrics"></div></div>'+block+'</section>')
s=s.replace('<a href="#players">TUYỂN THỦ</a><a href="#styles">PHONG CÁCH</a>','<a href="#players">TUYỂN THỦ</a>')
s=s.replace('<section class="player-section" id="styles">','<section class="cluster-subsection" id="styles">')
s=s.replace('.cluster-controls{','.cluster-subsection{margin-top:30px}.cluster-controls{')
p.write_text(s,encoding='utf-8')
