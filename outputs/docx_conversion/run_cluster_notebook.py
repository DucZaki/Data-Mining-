import nbformat
from nbclient import NotebookClient
from pathlib import Path
path=Path('notebooks/02_phan_cum_nguoi_choi.ipynb')
nb=nbformat.read(path,as_version=4)
client=NotebookClient(nb,timeout=600,kernel_name='python3',resources={'metadata':{'path':str(Path.cwd())}})
client.execute()
errors=[(i+1,o.get('evalue')) for i,c in enumerate(nb.cells) if c.cell_type=='code' for o in c.get('outputs',[]) if o.output_type=='error']
print('errors',errors,'code_cells',sum(c.cell_type=='code' for c in nb.cells))
if errors: raise SystemExit(1)
nbformat.write(nb,path)
