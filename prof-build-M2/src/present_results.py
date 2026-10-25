from IPython.display import HTML, display, clear_output
import matplotlib.pyplot as plt
from .contracts import validate_results
from .rendering import STYLE, body_sections

def present_results(results, provider_preview_rows: int = 100) -> None:
    clear_output(wait=False)
    plt.close('all')
    if isinstance(provider_preview_rows,bool) or not isinstance(provider_preview_rows,int) or provider_preview_rows<=0:
        raise ValueError('provider_preview_rows must be a positive integer')
    validate_results(results)
    display(HTML('<style>'+STYLE+'</style><main>'+''.join(body_sections(results,provider_preview_rows))+'</main>'))
