# constants.py

"""This module defines project-level constants."""

class ConstantsNamespace():
    __slots__ = ()
    # overall
    WARNING = "⚠️"
    ERROR = "🚨"
    INFO = "ℹ️"
    SUCCESS = "✅"
    
    # orbit compare
    COMP_SAMPLE_TIME = 60*5 # segundos
    COMP_NUMBER_SAMPLES = 80