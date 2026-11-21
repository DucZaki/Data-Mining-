from pathlib import Path
p=Path('scripts/09_build_public_dashboard.py'); s=p.read_text(encoding='utf-8'); anchor='    payload = json.dumps(data'
insert='''    # Keep the SQLite clustering cohort separate from the VCT radar cohort.
    from sklearn.cluster import AgglomerativeClustering
    from valorant_mining.clustering import prepare_matrix
    clustered = pd.read_csv(ROOT / "outputs" / "tables" / "player_clusters.csv")
    _, scaled = prepare_matrix(clustered)
    clustered["average_cluster"] = AgglomerativeClustering(n_clusters=2, linkage="average").fit_predict(scaled)
    fields = ["PlayerID", "PlayerName", "games", "cluster", "average_cluster", "adr", "deaths_pr", "assists_pr", "fk_pr", "fd_pr", "acs_sd", "hs"]
    data["cluster_players"] = json.loads(clustered[fields].to_json(orient="records", force_ascii=False, double_precision=5))
    data["cluster_sizes"] = clustered.groupby("cluster").size().to_dict()
    data["average_sizes"] = clustered.groupby("average_cluster").size().to_dict()
    data["cluster_profiles"] = json.loads(clustered.groupby("cluster")[["adr", "deaths_pr", "assists_pr", "fk_pr", "fd_pr", "acs_sd", "hs"]].mean().reset_index().to_json(orient="records", double_precision=5))
'''
assert anchor in s;s=s.replace(anchor,insert+anchor);p.write_text(s,encoding='utf-8')
p=Path('dashboard/public_template.html');s=p.read_text(encoding='utf-8');anchor='</main>\n<script>const DATA=';section='''<section class="player-section" id="styles"><div class="section-line"><div><h2>Phong cách tuyển thủ</h2></div><p>Chọn tuyển thủ để xem nhóm chỉ số thi đấu tương đồng.</p></div><div class="player-controls cluster-controls"><label>Tìm tuyển thủ<input id="clusterSearch" type="search" placeholder="Nhập tên tuyển thủ"></label><label>Tuyển thủ<select id="clusterSelect" aria-label="Chọn tuyển thủ phân cụm"></select></label></div><div class="cluster-grid"><div class="cluster-card"><h3 id="clusterName">—</h3><p id="clusterLabel"></p><div id="clusterStats"></div></div><div class="cluster-card"><h3>So sánh nhóm</h3><div id="clusterCompare"></div></div></div></section>
</main>
<script>const DATA=''';assert anchor in s;s=s.replace(anchor,section);s=s.replace('<a href="#players">TUYỂN THỦ</a>','<a href="#players">TUYỂN THỦ</a><a href="#styles">PHONG CÁCH</a>');s=s.replace('__PLAYER_CSS__','__PLAYER_CSS__\n.cluster-controls{grid-template-columns:1fr 1fr}.cluster-grid{display:grid;grid-template-columns:1fr 1fr;gap:15px}.cluster-card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:20px}.cluster-card h3{font:800 28px Barlow Condensed,Arial;margin:0 0 10px}.cluster-card p{color:var(--muted);font-size:13px}.cluster-stat{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-top:1px solid var(--line);font-size:13px}.cluster-stat b{color:var(--mint)}@media(max-width:700px){.cluster-grid{grid-template-columns:1fr}}');s=s.replace('__PLAYER_JS__','__PLAYER_JS__\n__CLUSTER_JS__');p.write_text(s,encoding='utf-8')
p=Path('scripts/09_build_public_dashboard.py');s=p.read_text(encoding='utf-8');s=s.replace('    output = ROOT / "dashboard" / "index.html"','    template = template.replace("__CLUSTER_JS__", (ROOT / "dashboard" / "player_clusters.js").read_text(encoding="utf-8"))\n    output = ROOT / "dashboard" / "index.html"');p.write_text(s,encoding='utf-8')

