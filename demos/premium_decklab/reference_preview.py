"""Record the reference adapter's real QWidget at 1500x970 and 1100x900."""
from reference import ReferenceWindow, ROOT
from record_preview import record

if __name__ == '__main__':
    record(ROOT / 'build/qa-decklab-finish', width=1500, height=970,
           window_factory=ReferenceWindow, main_name='decklab-full.png',
           small_height=900, export_art=False)
