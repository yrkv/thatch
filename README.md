
# Thatch


Collection of fairly minimal machine learning utilities.

Loosely inspired by systems such as Wandb and Aim, but trying to keep things simple and flexible. In particular, with a focus on modular design and conveniences.


### Modules

- `thatch.config` -- Configuration framework for assigning hyperparameter values.
    - Applying the `@configurable()` decorator to any function causes it to pull in default values for any **keyword-only** arguments.
    - Use the `configure(...)` context manager to apply configuration values within some context.
    - Contains utility functions for inspecting/listing `@configurable` functions, configurable parameters, or reading current configuration state.
        - Note: For any configuration key, it's advised to prefer adding it to
          the params of a `@configurable` function over using
          `read_config(key)`. Adding to the params of a function allows
          statically listing used config keys.
- `thatch.track` -- Experiment tracking library.
    - `Run()` creates a construct for tracking experimental values, as well as a number of utilities for recording that data and saving relevant artifacts (such as visualizations).
    - Saves run results to a `.thatch/` directory by default, or use `mem_root` submodule variants to save runs in-memory.
    - Contains utility functions for querying the data root. These can be used from within python as a library, invoked via shell, or even exposed as a web API.
    - Contains optional specification for reproducible/interruptible experiments. Implemented by saving checkpoints which contain **all** information that represents the current state and using a pure function that resumes from a checkpoint at each taken checkpoint.
        - Yes this slows things down quite a bit, so checkpoint frequency should be relatively low -- on the order of minutes to hours, not every step.
- `thatch.viz` -- Utilties library containing pre-made functions for various visualizations of Thatch outputs.
    - Use `matplotlib` to produce plot of a tracked variable aggregated over all runs in a (sub)root.
    - Interactive `ipywidgets` run data explorer(s).
        - Tabular cross-run performance comparisons.
        - (multi)image viewer.
        - Animation creator from saved outputs of a run. Can be interactive for viewing in Jupyter, using `ipywidgets`.
    - Eventually implement a Wandb/Aim style web dashboard too.
- `thatch.util` -- one-off utility functions or other simple conveniences which do not fall under any of the core modules.



### Old readme part
- ***Run*** -- Structure used to store/track all data related to a particular experiment, including both tracked values and metadata which applies to the entire run.
- ***Root*** -- Location used by a run to store/write its data.
	- `MemoryRoot`: Keep everything entirely in memory of current process; pretty much equivalent to using ad-hoc list(s) of entries.
	- `DirectoryRoot`: Write run data to files within a directory.


