"""Execute startup and default analysis without requesting an export."""
from pathlib import Path
import nbformat
from nbclient import NotebookClient
nb=nbformat.read('analysis.ipynb',as_version=4)
client=NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(Path.cwd())}})
client.execute()
Path('artifacts').mkdir(exist_ok=True)
nbformat.write(nb,'artifacts/analysis.executed.ipynb')
print('Notebook smoke passed:',len(nb.cells),'cells; no explicit export requested')
