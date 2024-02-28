"""
Utility functions and modules used by asyncui.
Some might be extracted to separate packages in the future.

Modules:
    callbacks - Utilities for simplifing callback function use
    context - Utilities for working with context managers inside classes
    coroutines - Provides coroutine based functions, simplifing things like UI alignment or data transformations
    descriptors - Utility descriptors for doing things like managing default or inferable attribute values
    transformers - Provides convenience functions for working with functions (T) -> T2, used by graphics for UI alignment.

Some utilities may be converted to separate packagges, in which case, alies will be provided here.
TODO: Coroutines should be renamed
NOTE: transformers & coroutines could be seperate modules
"""