const clustersById=new Map((DATA.cluster_players||[]).map(p=>[String(p.PlayerID),p]));
function renderSelectedCluster(profile){
 const target=$('#playerCluster');
 const p=clustersById.get(String(profile.player_id));
 if(!p){target.innerHTML='<strong>Chưa có nhóm phân cụm</strong><p>Tuyển thủ này không nằm trong tập đủ điều kiện phân cụm của dữ liệu thi đấu 2020–2022.</p>';return}
 const own=DATA.cluster_profiles.find(x=>x.cluster===p.cluster);
 const other=DATA.cluster_profiles.find(x=>x.cluster!==p.cluster);
 const label=own.fk_pr>other.fk_pr?'Thiên về giao tranh và mở đầu':'Thiên về hỗ trợ và ít tử vong hơn';
 const avgSize=DATA.average_sizes[p.average_cluster];
 target.innerHTML=`<strong>Nhóm ${Number(p.cluster)+1}: ${label}</strong>`;
}

